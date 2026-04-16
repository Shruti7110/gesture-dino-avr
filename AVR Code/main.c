#include <avr/io.h>
#include <util/delay.h>
#include <stdio.h>
#include "uart.h"
#include "i2c.h"
#include "adxl345.h"

int main(void)
{
	int16_t x, y, z;
	char buf[30];

	UART_Init();
	I2C_Init();
	ADXL345_Init();

	while(1)
	{
		ADXL345_ReadXYZ(&x, &y, &z);

		// Clean format ? Python parses this
		sprintf(buf, "%d,%d,%d\r\n", x, y, z);
		UART_SendString(buf);

		_delay_ms(100);    // 10Hz ? matches Edge Impulse training frequency
	}
}