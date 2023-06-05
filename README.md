
# AI-GasSensor-LowCost-HighPrecision

This project is a simple close system that aims to improve the precision and usability of simple, cheap, commercial MQ MQ(or similar) gas sensors in conjunction with AI and machine learning to correlate data from an N array of MQ (or similar) sensors.

## Description

Since there is a complete line-up of cheap and usable gas sensors, we aim to create a closed system for the DIY market to make accurate readings and reports about the general air quality.
This system can also be applied to any general-purpose electronic device in order to detect malfunctions(safety) and activate countermeasures that improve air quality.

Eg. 
3D printing:
- accurately detect smoke (Fire prevention).
- Activation of the air extractor when a set threshold is met.
- Halt printing in presence of a flammable gas detection.
- ...

general-purpose air quality system. Creation of a system on which a person or institution can rely to report air quality on a general basis:
- detection of gas leaks.
- Urban air quality monitoring.
- Automate gas venting mechanisms when gas is present a.e.(in institutions, buildings, parking lots, etc.).
- Fire prevention.
- ...

## Choosing the right Sensor for your application.

We provide a HTML code for a graph (graph.rar) to aid visualization of the sensitivities (ppm) and what gases each sensor reacts To. When designing you system you should take into account the following points: 
(The compression (.rar) of this file was necessary due to HTML having the required images encoded in base64 in it)

**(hypotetical - to be proven)** 
- To increase accuracy for a certain type of gas, you must pick multiple (different) sensors that have the same sensitivity for the same gases.(In this case, the network would take into consideration the multiple gain of a specific gas over the multiple sensors (for the same ppm range) and be able to correlate precisely what gas is present with a more accurate measure.)

- To increase reading range, you must pick multiple (different) sensors that read the same gas over different ppm ranges.(In this case, the network would take into consideration the multiple gains over a large ppm range and be able to correlate that gas more quickly with a small increase in precision.)


## Getting Started

TBD

### Dependencies

TBD

### Installing

TBD

### Executing program

TBD

## Help

TBD

## Authors

Contributors names and contact info

- Filipe Martins (twitter)@FilipeM36359770

## Version History

* 0.1
    * Initial Release

## Task List

- [x] Create a basic sensor sofware emulation (MQ-2, MQ-5 , MQ-9 and MQ 135)
- [ ] Implement the complete line-up for the MQ sensors
- [ ] Create a full gas chamber sofware emulation (with gas emitors and venting to accuratly graph ppms over a multitute of cases)
- [ ] Develop a Neural network to solve the problem and test multiple architectures
- [ ] Implementation on a MicroController

## License

This project is licensed under the GPL-3.0 License - see the LICENSE.md file for details

## Acknowledgments

Reversed enginnered to create the first implementation of a gas sensor emulation in software. Copy of the calibration logic that will be part of Implementation on a MicroController.
[sandboxelectronics.com](https://sandboxelectronics.com/?p=165)
