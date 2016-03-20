// Arduino code for water meter readout and sending over wireless link using nRF24L01 module
// J.Heyman
// nRF24L01 code adapted from: http://blog.riyas.org/2014/08/raspberry-pi-as-nrf24l01-base-station-internet-connected-wireless.html

#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
#include <RF24_config.h>

int value;
int previousvalue;

#define RED 0
#define SILVER 1
int currentstate=SILVER;

unsigned long nbRead=0;
unsigned long nbTurns=0;

#define HIGH_THRESHOLD 60
#define LOW_THRESHOLD  30

// MOSI is on pin 11
// MISO is on pin 12
// SCK is on pin 13
// CE is on pin 9, CSN is on pin 10
RF24 radio(9,10);

const uint64_t pipe = { 0xF0F0F0F0D2LL };
char message[30];

void setup() {

  //nRF24 configurations
  radio.begin();
  radio.setChannel(0x4c);
  radio.setAutoAck(1);
  radio.setRetries(15,15);
  radio.setDataRate(RF24_250KBPS);
  radio.setPayloadSize(32);
  radio.openWritingPipe(pipe);
  radio.startListening();
}
 
void sendMessage() {
    // send data over wireless link
    radio.stopListening();
    radio.write(&message,strlen(message));
    radio.startListening(); 
} 
 
void loop(){
  value = analogRead(A0)/4;
  nbRead++;
  
  if ((currentstate == SILVER) && (value > HIGH_THRESHOLD) && (previousvalue > HIGH_THRESHOLD)) {
    currentstate = RED;
  }
  
  if((currentstate == RED) && (value < LOW_THRESHOLD) && (previousvalue < LOW_THRESHOLD))  {
    currentstate = SILVER;
    nbTurns++;
    sprintf(message, "water:top:%d", nbTurns);
    sendMessage();  
  } else if ((nbRead % 50) == 0) {
    sprintf(message, "water:alive");
    sendMessage(); 
  }
  
  // Loop at 10 Hz
  previousvalue = value;
  delay(100);
}
