# Robotiq Gripper Description Package (`robotiq_description`)

This package provides dynamic URDF descriptions and ROS 2 Control launch configurations for the **Robotiq 2F-85** and **Robotiq 2F-140** adaptive grippers.

The modular launch system allows users to easily start either a **single** or **dual gripper configuration**, automatically configuring the appropriate hardware interfaces, namespaces, and controllers.

---

## Features

* Support for Robotiq 2F-85 and 2F-140 grippers
* Single and dual gripper configurations
* Automatic ROS 2 Control controller loading
* Namespace isolation for dual gripper setups (`/left` and `/right`)
* Automatic serial port detection
* Support for:

  * Real hardware
  * Mock hardware (`mock_components`)
  * Gazebo simulation
  * Isaac Sim integration

---

# Quick Start

## Launch a Single Robotiq 2F-140 (Default)

By default, the launch file starts a single Robotiq 2F-140 gripper.

```bash
ros2 launch robotiq_description robotiq_control.launch.py
```

---

## Launch a Single Robotiq 2F-85

To launch a Robotiq 2F-85 gripper, specify the gripper type:

```bash
ros2 launch robotiq_description robotiq_control.launch.py gripper_type:=85
```

---

## Launch Dual Grippers

To launch two grippers simultaneously, enable the `is_dual` flag.

Example:

```bash
ros2 launch robotiq_description robotiq_control.launch.py gripper_type:=85 is_dual:=true
```

---

# Launch Arguments

The following launch arguments are available:

| Argument            | Default       | Type / Choices  | Description                                     |
| ------------------- | ------------- | --------------- | ----------------------------------------------- |
| `gripper_type`      | `140`         | `85`, `140`     | Selects the Robotiq gripper model.              |
| `is_dual`           | `false`       | `true`, `false` | Launches two independent grippers.              |
| `com_port`          | Auto-detected | `/dev/ttyACM*`  | Serial port for single gripper setups.          |
| `com_port_left`     | Auto-detected | `/dev/ttyACM*`  | Serial port for the left gripper in dual mode.  |
| `com_port_right`    | Auto-detected | `/dev/ttyACM*`  | Serial port for the right gripper in dual mode. |

---

# Real Hardware Usage

To connect to actual Robotiq grippers:

```bash
ros2 launch robotiq_description robotiq_control.launch.py
```

For dual grippers:

```bash
ros2 launch robotiq_description robotiq_control.launch.py is_dual:=true
```

---

# Automatic Port Detection

The launch system includes a Python helper utility that automatically scans connected USB devices and identifies compatible Robotiq/Espressif serial adapters.

When detected, the appropriate ports are automatically assigned without requiring manual configuration.

Typical detected devices:

```text
/dev/ttyUSB0
/dev/ttyUSB1
/dev/ttyACM0
```

Manual port specification can still be provided using:

```bash
com_port:=...
com_port_left:=...
com_port_right:=...
```

---


# Dual Gripper Namespaces

When `is_dual:=true` is used, two completely independent controller managers are launched:

```text
/left/controller_manager
/right/controller_manager
```

Controllers become:

```text
/left/robotiq_gripper_controller
/right/robotiq_gripper_controller
```


This enables independent control of each gripper.


---

# Example Configurations

## Single 2F-140 Simulation

```bash
ros2 launch robotiq_description robotiq_control.launch.py
```

---

## Single 2F-85 Simulation

```bash
ros2 launch robotiq_description robotiq_control.launch.py gripper_type:=85
```

---

## Dual Real Hardware

```bash
ros2 launch robotiq_description robotiq_control.launch.py is_dual:=true
```

---

# License

This package is distributed under the same license as the parent project.
