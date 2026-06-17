import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
import serial.tools.list_ports

def get_ports():
    """Finds all ports with Robotiq/Espressif HWIDs, sorted for stability."""
    devs = sorted([p.device for p in serial.tools.list_ports.comports() if any(h in p.hwid for h in ["303A", "0403"])])
    dev_1 = devs[0] if len(devs) > 0 else "/dev/ttyACM0"
    dev_2 = devs[1] if len(devs) > 1 else "/dev/ttyACM1"
    return dev_1, dev_2

def generate_launch_description():
    dev_1, dev_2 = get_ports()

    is_dual = LaunchConfiguration("is_dual")
    gripper_type = LaunchConfiguration("gripper_type")
    model = LaunchConfiguration("model")
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    
    ctrl_yaml = [
        FindPackageShare("robotiq_description"), 
        "/config/robotiq_controllers_", gripper_type, ".yaml"
    ]

    args = [
        DeclareLaunchArgument("gripper_type", default_value="140", choices=["85", "140"], 
                              description="Type of gripper: '85' or '140'"),
        DeclareLaunchArgument("is_dual", default_value="false", 
                              description="Set to 'true' to launch dual grippers"),
        
        DeclareLaunchArgument("model", default_value=[
            FindPackageShare("robotiq_description"), 
            "/urdf/robotiq_2f_", gripper_type, "_gripper.urdf.xacro"
        ]),
        
        DeclareLaunchArgument("com_port", default_value=dev_1),
        DeclareLaunchArgument("use_fake_hardware", default_value="false"),
        DeclareLaunchArgument("tf_prefix", default_value=""),
        DeclareLaunchArgument("com_port_left", default_value=dev_1),
        DeclareLaunchArgument("com_port_right", default_value=dev_2),
    ]

    nodes = []
    
    # SINGLE GRIPPER SETUP

    robot_desc_single = ParameterValue(Command([
        FindExecutable(name="xacro"), " ", model,
        " use_fake_hardware:=", use_fake_hardware, " com_port:=", LaunchConfiguration("com_port"),
        " prefix:=", LaunchConfiguration("tf_prefix")
    ]), value_type=str)

    nodes.extend([
        Node(package="controller_manager", executable="ros2_control_node", 
             parameters=[{"robot_description": robot_desc_single}, ctrl_yaml], 
             output="screen", condition=UnlessCondition(is_dual)),
             
        Node(package="robot_state_publisher", executable="robot_state_publisher", 
             parameters=[{"robot_description": robot_desc_single}], 
             output="screen", condition=UnlessCondition(is_dual))
    ])

    for ctrl in ["joint_state_broadcaster", "robotiq_gripper_controller", "robotiq_activation_controller"]:
        nodes.append(Node(package="controller_manager", executable="spawner", 
                          arguments=[ctrl], condition=UnlessCondition(is_dual)))

    # DUAL GRIPPER SETUP

    for side, port in [("left", "com_port_left"), ("right", "com_port_right")]:
        prefix = f"{side}_"
        
        desc_dual = ParameterValue(Command([
            FindExecutable(name="xacro"), " ", model,
            " use_fake_hardware:=", use_fake_hardware, " com_port:=", LaunchConfiguration(port), 
            " prefix:=", prefix
        ]), value_type=str)

        nodes.extend([
            Node(package="controller_manager", executable="ros2_control_node", 
                 namespace=side, parameters=[{"robot_description": desc_dual}, ctrl_yaml], 
                 condition=IfCondition(is_dual)),
                 
            Node(package="robot_state_publisher", executable="robot_state_publisher", 
                 namespace=side, parameters=[{"robot_description": desc_dual}], 
                 condition=IfCondition(is_dual))
        ])

        for ctrl in ["joint_state_broadcaster", "robotiq_activation_controller", "robotiq_gripper_controller"]:
            nodes.append(Node(package="controller_manager", executable="spawner",
                              arguments=[ctrl, "-c", f"/{side}/controller_manager"], 
                              condition=IfCondition(is_dual)))

    return LaunchDescription(args + nodes)