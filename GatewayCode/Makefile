# Makefile for LoRa Multi-Channel Gateway on Raspberry Pi CM4
# Compiler: g++
# Libraries: WiringPi, pthreads

CXX = g++
CXXFLAGS = -O3 -Wall -std=c++11 -Iinclude
LDFLAGS = -lwiringPi -lpthread

TARGET = lora_gw_3ch
SRCS = src/main_gw.cpp src/sx1278_wiringpi.cpp
OBJS = $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(OBJS) -o $(TARGET) $(LDFLAGS)
	@echo "Build complete: ./$(TARGET)"

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f src/*.o $(TARGET) gateway_log_*.csv
	@echo "Cleaned build artifacts."

.PHONY: all clean
