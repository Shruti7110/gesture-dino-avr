
#ifndef UART_H_
#define UART_H_

#include <avr/io.h>

// CPU and BAUD rate define
#define F_CPU 16000000UL
#define BAUD 9600
#define UBRR_VAL ((F_CPU/16/BAUD) - 1) // formula to calculate baud register value

// Function declarations
void UART_Init(void);
void UART_SendChar(char c);
void UART_SendString(const char *str);



#endif /* UART_H_ */
