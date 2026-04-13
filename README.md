# ros2_robotiq_gripper

This repository contains the ROS 2 driver, controller and description packages for working with a Robotiq Gripper.

The goal is to support multiple Robotiq Grippers.

Initially this repo supported only the 2f-85 however we want to also support the e-pick and pull requests are welcome for other grippers.
- https://github.com/PickNikRobotics/ros2_epick_gripper


## Build status

Currently the `main` branch is used for all current releases: Humble, Iron and Rolling.
As this is not a core ROS 2 package API/ABI breakage is not guaranteed, it is done as best effort and takes into account maintenance costs.
This is not sponsored or maintained by Robotiq we try to keep everything on main to reduce maintenance overhead.


ROS2 Distro | Branch | Build status | Documentation | Released packages
:---------: | :----: | :----------: | :-----------: | :---------------:
**Rolling** | [`main`](https://github.com/PickNikRobotics/ros2_robotiq_gripper/tree/main) | [![Rolling Binary Build](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/rolling-binary-build-main.yml/badge.svg?branch=main)](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/rolling-binary-build-main.yml?branch=main) <br /> [![Rolling Semi-Binary Build](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/rolling-semi-binary-build-main.yml/badge.svg?branch=main)](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/rolling-semi-binary-build-main.yml?branch=main) | | [ros2_robotiq_gripper](https://index.ros.org/p/ros2_robotiq_gripper/github-PickNikRobotics-ros2_robotiq_grippper/#rolling)


ROS2 Distro | Branch | Build status | Documentation | Released packages
:---------: | :----: | :----------: | :-----------: | :---------------:
**Humble** | [`main`](https://github.com/PickNikRobotics/ros2_robotiq_gripper/tree/main) | [![Humble Binary Build](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/humble-binary-build-main.yml/badge.svg?branch=main)](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/humble-binary-build-main.yml?branch=main) <br /> [![Humble Semi-Binary Build](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/humble-semi-binary-build-main.yml/badge.svg?branch=main)](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/humble-semi-binary-build-main.yml?branch=main) | | [ros2_robotiq_gripper](https://index.ros.org/p/ros2_robotiq_gripper/github-PickNikRobotics-ros2_robotiq_grippper/#humble)


ROS2 Distro | Branch | Build status | Documentation | Released packages
:---------: | :----: | :----------: | :-----------: | :---------------:
**Iron** | [`main`](https://github.com/PickNikRobotics/ros2_robotiq_gripper/tree/main) | [![Iron Binary Build](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/iron-binary-build-main.yml/badge.svg?branch=main)](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/iron-binary-build-main.yml?branch=main) <br /> [![Iron Semi-Binary Build](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/iron-semi-binary-build-main.yml/badge.svg?branch=main)](https://github.com/PickNikRobotics/ros2_robotiq_gripper/actions/workflows/iron-semi-binary-build-main.yml?branch=main) | | [ros2_robotiq_gripper](https://index.ros.org/p/ros2_robotiq_gripper/github-PickNikRobotics-ros2_robotiq_grippper/#iron)

### Explanation of different build types

**NOTE**: There are three build stages checking current and future compatibility of the package.

[Detailed build status](.github/workflows/README.md)

1. Binary builds - against released packages (main and testing) in ROS distributions. Shows that direct local build is possible.

   Uses repos file: `$NAME$-not-released.<ros-distro>.repos`

1. Semi-binary builds - against released core ROS packages (main and testing), but the immediate dependencies are pulled from source.
   Shows that local build with dependencies is possible and if fails there we can expect that after the next package sync we will not be able to build.

   Uses repos file: `$NAME$.repos`

1. Source build - also core ROS packages are build from source. It shows potential issues in the mid future.

---

## Extended State Feedback: Effort Reporting & Object Detection

Extending the standard Robotiq driver with richer gripper state feedback, surfacing two new data channels from raw Modbus registers up to the `ros2_control` real-time loop:

- **Gripper Current (Effort)** — motor current draw (Modbus byte 5) scaled to Newtons and exported as `HW_IF_EFFORT`. Allows controllers to distinguish an empty closed gripper from one actively holding a part.
- **Object Detection Status** — firmware status code exported as `"object_detection_status"`, indicating whether an object was grasped (`1` = outer, `2` = inner), missed (`3` = stall/no object), or fingers are still moving (`0`). Enables reliable grasp confirmation without blind timeouts.

**Additional optimisation:** Modbus write commands are suppressed when speed, force, and position have not changed since the previous cycle, reducing unnecessary bus contention during steady-state hold.

### URDF Configuration

Add the two new state interfaces to your `ros2_control` joint definition:

```xml
<state_interface name="position"/>
<state_interface name="velocity"/>
<state_interface name="effort"/>
<state_interface name="object_detection_status"/>
```

The driver accepts 2, 3, or 4 state interfaces — partial adoption is supported.

---

## Documentation

The `documentation/` folder contains resources for exploring the driver architecture:

- **`robotiq_driver_ontology.owl`** — An OWL semantic web ontology that formally maps the full `robotiq_driver` C++ architecture: Modbus register payload layout, thread boundaries, ROS 2 hardware interfaces, and dependency-injection factories.

- **`agent.py`** — A Python CLI tool that parses the ontology and uses the OpenAI API to answer natural language questions about the codebase via auto-generated SPARQL queries. Example questions:
  - *"What are the packages in this project and what is their purpose?"*
  - *"What are the four possible Object Detection Status values, and what integer code corresponds to a stall?"*

To use the agent: navigate to `documentation/`, configure your OpenAI API key in `.env`, install dependencies with `pip install -r requirements.txt`, then run `python3 agent.py`.