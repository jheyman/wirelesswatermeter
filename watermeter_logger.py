#!/usr/bin/python
# -*- coding: utf-8 -*-

from nrf24 import NRF24
import time

pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]

radio = NRF24()
radio.begin(0, 0, 25, 7)

radio.setRetries(15,15)

radio.setPayloadSize(32)
radio.setChannel(0x60)
radio.setDataRate(NRF24.BR_250KBPS)
radio.setPALevel(NRF24.PA_MIN)

radio.setAutoAck(True)
radio.enableDynamicPayloads()
radio.enableAckPayload()

radio.openWritingPipe(pipes[0])
radio.openReadingPipe(1, pipes[1])

radio.startListening()
radio.stopListening()

radio.printDetails()

radio.startListening()

c=1
while True:
    pipe = [0]
    # wait for incoming packet from transmitter
    while not radio.available(pipe):
        time.sleep(10000/1000000.0)

    recv_buffer = []
    radio.read(recv_buffer, radio.getDynamicPayloadSize())
    print recv_buffer

