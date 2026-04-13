import os
import sys
import re
from dotenv import load_dotenv
from openai import OpenAI
import rdflib

# Load environment variables from .env
load_dotenv()

def extract_ontology_schema(g):
    """
    Extracts a summary of the classes and properties from the graph
    to provide context to the LLM.
    """
    classes = set()
    properties = set()
    
    # Query for Classes
    class_query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?c WHERE {
        { ?c a owl:Class } UNION { ?c a rdfs:Class }
        FILTER(isIRI(?c))
    }
    """
    for row in g.query(class_query):
        uri = str(row[0])
        name = uri.split('#')[-1] if '#' in uri else uri.split('/')[-1]
        classes.add(name)

    # Query for Properties (Object and Datatype)
    prop_query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?p WHERE {
        { ?p a owl:ObjectProperty } UNION { ?p a owl:DatatypeProperty }
        FILTER(isIRI(?p))
    }
    """
    for row in g.query(prop_query):
        uri = str(row[0])
        name = uri.split('#')[-1] if '#' in uri else uri.split('/')[-1]
        properties.add(name)

    return sorted(list(classes)), sorted(list(properties))

def execute_sparql(g, query_string):
    """
    Executes a SPARQL query and formats the results into a string.
    """
    try:
        results = g.query(query_string)
        output_lines = []
        
        has_results = False
        for i, row in enumerate(results):
            has_results = True
            formatted_row = []
            for item in row:
                if isinstance(item, rdflib.term.URIRef):
                    formatted_row.append(item.split('#')[-1] if '#' in item else str(item).split('/')[-1])
                elif item is None:
                    formatted_row.append("<null>")
                else:
                    formatted_row.append(str(item))
            output_lines.append(f"{i+1}. " + " | ".join(formatted_row))
            
        if not has_results:
            return "(No results found matching your query)"
        return "\n".join(output_lines)
    except Exception as e:
        return f"Error executing SPARQL query: {e}"

def extract_query_from_text(text):
    """
    Extracts SPARQL query from markdown blocks.
    """
    match = re.search(r'```sparql(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'```(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        print("Error: OPENAI_API_KEY is not set correctly in the .env file.")
        sys.exit(1)

    print("Initializing OpenAI client...")
    client = OpenAI(api_key=api_key)

    ontology_path = os.path.join(os.path.dirname(__file__), "robotiq_driver_ontology.owl")
    if not os.path.exists(ontology_path):
        print(f"Error: Could not find ontology file at {ontology_path}")
        sys.exit(1)

    print("Loading ontology graph...")
    g = rdflib.Graph()
    try:
        g.parse(ontology_path, format="xml")
    except Exception as e:
        print(f"Error parsing ontology: {e}")
        sys.exit(1)

    print(f"Loaded {len(g)} triples.")
    
    print("Extracting schema for the AI agent...")
    available_classes, available_props = extract_ontology_schema(g)
    print(f"Found {len(available_classes)} classes and {len(available_props)} properties.")

    print("\n================================================")
    print("Welcome to the Reasoning Robotiq Ontology Agent")
    print("Type 'exit' or 'quit' to quit.")
    print("================================================\n")

    # The base system prompt provides the schema and the rules of engagement
    system_prompt = f"""
You are an expert semantic web reasoning agent. Your task is to answer user questions about a C++ ROS 2 driver ontology for the Robotiq 2F Gripper.
The primary namespace is 'http://www.semanticweb.org/robotiq_driver/ontology#'. Use 'PREFIX robotiq: <http://www.semanticweb.org/robotiq_driver/ontology#>'

Here is the schema extracted from the ontology:
AVAILABLE CLASSES: {', '.join(available_classes)}
AVAILABLE PROPERTIES: {', '.join(available_props)}

WORKFLOW INSTRUCTIONS:
1. MANDATORY: Your FIRST attempt MUST be a completely open exploratory query. You are STRICTLY FORBIDDEN from guessing relationships or using specific class/property names in Attempt 1. 
2. Your Attempt 1 query MUST look exactly like this structure, using only regex filters on ?s, ?p, and ?o:
   PREFIX robotiq: <http://www.semanticweb.org/robotiq_driver/ontology#>
   SELECT ?s ?p ?o WHERE {{
       ?s ?p ?o .
       FILTER(regex(str(?s), "YOUR_KEYWORD", "i") || regex(str(?o), "YOUR_KEYWORD", "i") || regex(str(?p), "YOUR_KEYWORD", "i"))
   }} LIMIT 25
3. Enclose all queries strictly within ```sparql ... ``` blocks.
4. The system will execute the query and provide you with the raw triples.
5. Analyze those raw triples. If the results DO NOT contain the information needed to answer the user's question, your NEXT attempt MUST be another exploratory query using a DIFFERENT keyword (e.g., if "serial" fails, try "byte", "register", or "response").
6. Once you map the ACTUAL relationships in the graph from your explorations, write a precise SPARQL query using the exact structure you discovered.
7. CRITICAL: DO NOT output a final natural language response unless you have successfully retrieved the specific data requested by the user. Do not state generic facts. 
8. If you have the final answer, output a natural language response. DO NOT output any more SPARQL blocks once you have the answer.
"""

    while True:
        try:
            user_input = input("Ask a question: ")
            if user_input.strip().lower() in ['exit', 'quit']:
                break
            if not user_input.strip():
                continue

            # Initialize conversation history for this specific question
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]

            max_attempts = 5
            attempts = 0
            final_answer_reached = False

            while attempts < max_attempts and not final_answer_reached:
                print(f"  [Agent is thinking... Attempt {attempts + 1}/{max_attempts}]")
                response = client.chat.completions.create(
                    model="gpt-5.4",
                    messages=messages,
                    temperature=0.0
                )
                
                agent_message = response.choices[0].message.content
                messages.append({"role": "assistant", "content": agent_message})

                sparql_query = extract_query_from_text(agent_message)

                if sparql_query:
                    print("\n--- Agent Generated Query ---")
                    print(sparql_query)
                    print("-----------------------------")
                    
                    results_text = execute_sparql(g, sparql_query)
                    print(f"--- Query Results ---\n{results_text}\n---------------------\n")
                    
                    # Feed the results back to the agent
                    feedback = f"Query Execution Results:\n{results_text}\nIf this answers the user's question, provide the final answer. If it failed or returned no results, generate a new, corrected SPARQL query."
                    messages.append({"role": "user", "content": feedback})
                    attempts += 1
                else:
                    # If no SPARQL block is found, assume the agent is providing the final answer
                    print("\nAgent Final Response:")
                    print(agent_message)
                    print("\n")
                    final_answer_reached = True

            if not final_answer_reached:
                print("\nAgent Reached maximum query attempts. It could not find the exact answer.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()