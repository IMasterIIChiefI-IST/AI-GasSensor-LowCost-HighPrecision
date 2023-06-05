#include <TensorFlowLite_ESP32.h>

// Define the input shape of the neural network
const byte inputSize = 8;

// Define the output shape of the neural network
const byte outputSize = 11;

// Define the input and output tensors
TfLiteTensor* input;
TfLiteTensor* output;

// Define the model buffer and its size
uint8_t* modelBuffer;
int modelSize = 0;

// Define the 2-bit variable (4 sensors)
byte twoBitVariable = 0;

// From the TECHNICAL DATA graphs:
// Clean_Air_RS/Ro[4] = {.9777, .7999, .9956, .5563}; //  Clean_Air_RS/Ro  = Log10(graph_clean_air)
// The resistance used when generating the TECHNICAL DATA graphs
// Ro_defaults[4] = {10, 20, 10, 20};
// Rs_CLEAN_AIR[4] = {9.777, 15.998, 9.956, 11.126}; // Rs_CLEAN_AIR = Rl_defaults[i] * Clean_Air_RS/Ro[i]
// The real resistance used on the modules or you schematics measured by multimeter
const float Ro = {.998, .989, .996, 1.984};
// RO_CLEAR_AIR_FACTOR=(Sensor resistance in clean air)/RO, which is derived from the chart in datasheet
const float Ro_CLEAN_AIR_FACTOR = {9.796593186372746, 16.17593528816987, 9.995983935742972, 5.607862903225807};

// Array that registers the last read values
short int currentValues[4] = { 0, 0, 0, 0 };

// Array that registers the derivation bettween a-1 and a samples
short int derivationValues[4] = { 0, 0, 0, 0 };

// Defines the gas thresholds for the sensors safe levels for 8hrs
const byte H2 200;
const uint16_t LPG 500;
const uint16_t CH4 1000;
const byte CO 100;
const uint16_t Alcohol 500;
const byte smoke 200;
const uint16_t Propane 1000;
const uint16_t CO2 5000;
const byte NH4 35;
const byte Tolueno 150;
const uint16_t Acetona 500;

// Defines the MAX gas thresholds for the sensors
const uint16_t H2_Max 1500;
const uint16_t LPG_Max 800;
const uint16_t CH4_Max 2000;
const uint16_t CO_Max 1200;
const uint16_t Alcohol_Max 5000;
const uint16_t smoke_Max 400;
const uint16_t Propane_Max 10000;
const uint16_t CO2_Max 5000;
const uint16_t NH4_Max 300;
const uint16_t Tolueno_Max 500;
const uint16_t Acetona_Max 3000;

// Create a neural network object
ANN network;

void timerISR() {
  // Increment the 2-bit variable
  twoBitVariable = (twoBitVariable + 1) % 4;

  // Send the two-bit variable to GPIO pins
  digitalWrite(12, twoBitVariable & 0x01);         // Lower bit (GPIO 12)
  digitalWrite(14, (twoBitVariable >> 1) & 0x01);  // Higher bit (GPIO 14)

  // Run the neural network on the fourth cycle
  if (twoBitVariable == 3) {
    // Perform neural network prediction
    float inputs[inputSize] = { currentValues[0], currentValues[1], currentValues[2], currentValues[3], derivationValues[0], derivationValues[1], derivationValues[2], derivationValues[3], };
    memcpy(input->data.f, inputData, inputSize * sizeof(float));
    // Run the inference
    interpreter->Invoke();
    // Get the output data
    float outputData[outputSize];
    memcpy(outputData, output->data.f, outputSize * sizeof(float));
  }
}

void setup() {

  // Set GPIO pins as outputs
  pinMode(12, OUTPUT);
  pinMode(14, OUTPUT);

  digitalWrite(ESP8266_LED, HIGH);
  // Calibrating Sensors MQ2
  twoBitVariable = 0;
  digitalWrite(12, twoBitVariable & 0x01);         // Lower bit (GPIO 12)
  digitalWrite(14, (twoBitVariable >> 1) & 0x01);  // Higher bit (GPIO 14)
  Ro[twoBitVariable] = MQCalibration();
  // Calibrating Sensors MQ5
  twoBitVariable = 1;
  digitalWrite(12, twoBitVariable & 0x01);         // Lower bit (GPIO 12)
  digitalWrite(14, (twoBitVariable >> 1) & 0x01);  // Higher bit (GPIO 14)
  Ro[twoBitVariable] = MQCalibration();
  // Calibrating Sensors MQ9
  twoBitVariable = 2;
  digitalWrite(12, twoBitVariable & 0x01);         // Lower bit (GPIO 12)
  digitalWrite(14, (twoBitVariable >> 1) & 0x01);  // Higher bit (GPIO 14)
  Ro[twoBitVariable] = MQCalibration();
  // Calibrating Sensors MQ135
  twoBitVariable = 3;
  digitalWrite(12, twoBitVariable & 0x01);         // Lower bit (GPIO 12)
  digitalWrite(14, (twoBitVariable >> 1) & 0x01);  // Higher bit (GPIO 14)
  Ro[twoBitVariable] = MQCalibration();
  digitalWrite(ESP8266_LED, LOW);

  // Set up the timer interrupt
  timer1_attachInterrupt(timerISR);
  timer1_enable(TIM_DIV256, TIM_EDGE, TIM_LOOP);
  // Counter Value = (160 MHz) / (256 * 1 Hz)
  // CPU CLOCK / (Prescaler Value * Desired Frequency)
  timer1_write(62500);

  // Load the TFLite model into memory
  // Replace "model.tflite" with the name of your model file
  if (modelBuffer != nullptr) {
    free(modelBuffer);
    modelBuffer = nullptr;
  }
  File modelFile = SPIFFS.open("/model.tflite", "r");
  modelSize = modelFile.size();
  modelBuffer = (uint8_t*) malloc(modelSize);
  modelFile.read(modelBuffer, modelSize);
  modelFile.close();
  interpreter->SetModel(modelBuffer);

  // Create a TensorFlow Lite interpreter
  static tflite::MicroErrorReporter microReporter;
  static tflite::ErrorReporter* reporter = &microReporter;
  static tflite::ops::micro::AllOpsResolver resolver;
  static tflite::MicroInterpreter staticInterpreter(modelBuffer, resolver, reporter);
  interpreter = &staticInterpreter;

  // Allocate tensor buffers
  interpreter->AllocateTensors();

  // Get the input and output tensors
  input = interpreter->input(0);
  output = interpreter->output(0);

  // Set the input tensor shape
  input->dims->data[0] = 1;
  input->dims->data[1] = inputSize;
}

void loop() {
  delayMicroseconds(10);  // ADC DELAY
  float adc = MQRead();
  derivationValues[twoBitVariable] = derivationValues[twoBitVariable] - adc;
  currentValues[twoBitVariable] = adc;
}

/***************************** MQCalibration ****************************************
Input:   mq_pin - analog channel
Output:  Ro of the sensor
Remarks: This function assumes that the sensor is in clean air. It use  
         MQResistanceCalculation to calculates the sensor resistance in clean air 
         and then divides it with RO_CLEAN_AIR_FACTOR. RO_CLEAN_AIR_FACTOR is about 
         10, which differs slightly between different sensors.

Input:   raw_adc - raw value read from adc, which represents the voltage
Output:  the calculated sensor resistance
Remarks: The sensor and the load resistor forms a voltage divider. Given the voltage
         across the load resistor and its resistance, the resistance of the sensor
         could be derived.

int CALIBARAION_SAMPLE_TIMES=50;                    //define how many samples you are going to take in the calibration phase
int CALIBRATION_SAMPLE_INTERVAL=500;                //define the time interal(in milisecond) between each samples in the
                                                    //cablibration phase
/************************************************************************************/
float MQCalibration() {
  float val = 0;
  for (byte i = 0; i < 50; i++) {  //take multiple samples
    uint16_t raw_adc = analogRead(A0);
    val += ((float)Ro[twoBitVariable] * (1023 - raw_adc) / raw_adc);
    delay(500);
  }
  return (val / 50) / Ro_CLEAN_AIR_FACTOR[twoBitVariable];  //calculate the average value and divided by RO_CLEAN_AIR_FACTOR yields the Ro
}

/*****************************  MQRead *********************************************
Input:   mq_pin - analog channel
Output:  Rs of the sensor
Remarks: This function use MQResistanceCalculation to caculate the sensor resistenc (Rs).
         The Rs changes as the sensor is in the different consentration of the target
         gas. The sample times and the time interval between samples could be configured
         by changing the definition of the macros.

Input:   raw_adc - raw value read from adc, which represents the voltage
Output:  the calculated sensor resistance
Remarks: The sensor and the load resistor forms a voltage divider. Given the voltage
         across the load resistor and its resistance, the resistance of the sensor
         could be derived.

int READ_SAMPLE_INTERVAL=50;                        //define how many samples you are going to take in normal operation
int READ_SAMPLE_TIMES=5;                            //define the time interal(in milisecond) between each samples in 
                                                    //normal operation
************************************************************************************/
float MQRead() {
  float rs = 0;
  for (byte i = 0; i < 5; i++) {
    uint16_t raw_adc = analogRead(A0);
    rs += ((float)Ro[twoBitVariable] * (1023 - raw_adc) / raw_adc);
    delay(50);
  }
  return rs / 5;
}
