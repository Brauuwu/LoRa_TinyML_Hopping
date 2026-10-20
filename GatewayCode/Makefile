# Makefile for LoRa Multi-Channel Gateway on Raspberry Pi CM4
# Compiler: g++
# Libraries: WiringPi, pthreads

CXX = g++
CXXFLAGS = -O3 -Wall -std=c++11 -Iinclude
LDFLAGS = -lwiringPi -lpthread

# ── Gateway chính (3 kênh) ──
TARGET_GW = lora_gw_3ch
SRCS_GW = src/main_gw.cpp src/sx1278_wiringpi.cpp
OBJS_GW = $(SRCS_GW:.cpp=.o)

# ── Chương trình test truyền thông ──
TARGET_TEST = test_comm
SRCS_TEST = src/test_comm.cpp src/sx1278_wiringpi.cpp

all: $(TARGET_GW) $(TARGET_TEST)

# Build Gateway
$(TARGET_GW): $(OBJS_GW)
	$(CXX) $(OBJS_GW) -o $(TARGET_GW) $(LDFLAGS)
	@echo "Build complete: ./$(TARGET_GW)"

# Build Communication Test
$(TARGET_TEST): src/test_comm.o src/sx1278_wiringpi.o
	$(CXX) src/test_comm.o src/sx1278_wiringpi.o -o $(TARGET_TEST) $(LDFLAGS)
	@echo "Build complete: ./$(TARGET_TEST)"

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Build chỉ gateway
gateway: $(TARGET_GW)

# Build chỉ test
test: $(TARGET_TEST)

clean:
	rm -f src/*.o $(TARGET_GW) $(TARGET_TEST) gateway_log_*.csv
	@echo "Cleaned build artifacts."

.PHONY: all clean gateway test
