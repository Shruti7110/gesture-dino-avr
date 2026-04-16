
#include "uart.h"


void UART_Init(void){
	// Step 1: Set Baud rate
	UBRR0H = (uint8_t)(UBRR_VAL >> 8); // upper byte of baud value
	UBRR0L = (uint8_t)(UBRR_VAL); // lower byte of baud value
	
	//Step 2: Enable transmitter and receiver // This status register might change all the values if not set right
	UCSR0B = ( 1 << TXEN0 ) | ( 1 << RXEN0 ); // Value =  0b00011000
	
	// Step 3: Set frame format -> 8 data bits, 1 stop bit, no parity
	UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);	 
	// UCSR0C = (1 << UPM00) | (1 << UPM01); // uncomment to enable odd parity
	// UCSR0C = (1 << USBS0); // uncomment to set no of stop bits as 2
}

void UART_SendChar(char c){
	// Wait until the transmitting buffer is empty
	while (!(UCSR0A & (1 << UDRE0)));
	// Put character into buffer ? sends automatically
	UDR0 = c;
	
}

void UART_SendString(const char *str){
	// loop through string until null terminator
	while (*str != '\0')
	{
		UART_SendChar(*str);
		str++;         // move to next character
	}
	
}