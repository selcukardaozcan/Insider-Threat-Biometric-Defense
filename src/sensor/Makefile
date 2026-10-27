CC ?= gcc
CFLAGS ?= -Wall -Wextra -O2 -fPIC
LDFLAGS ?= -lrt

TARGET = keystroke_collector
SO_TARGET = libkeystroke_hook.so

all: $(TARGET) $(SO_TARGET)

$(TARGET): keystroke_collector.c
	$(CC) $(CFLAGS) -o $(TARGET) keystroke_collector.c $(LDFLAGS)

$(SO_TARGET): keystroke_collector.c
	$(CC) $(CFLAGS) -shared -o $(SO_TARGET) keystroke_collector.c $(LDFLAGS)

clean:
	rm -f $(TARGET) $(SO_TARGET) *.o

.PHONY: all clean
