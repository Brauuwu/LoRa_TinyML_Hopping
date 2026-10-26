#ifndef SX1278_WIRINGPI_H
#define SX1278_WIRINGPI_H

#include <stdint.h>
#include <string>
#include <mutex>

// Các thanh ghi quan trọng của Semtech SX1278
#define REG_FIFO                    0x00
#define REG_OP_MODE                 0x01
#define REG_FRF_MSB                 0x06
#define REG_FRF_MID                 0x07
#define REG_FRF_LSB                 0x08
#define REG_PA_CONFIG               0x09
#define REG_FIFO_ADDR_PTR           0x0D
#define REG_FIFO_TX_BASE_ADDR       0x0E
#define REG_FIFO_RX_BASE_ADDR       0x0F
#define REG_FIFO_RX_CURRENT_ADDR    0x10
#define REG_IRQ_FLAGS               0x12
#define REG_RX_NB_BYTES             0x13
#define REG_PKT_SNR_VALUE           0x19
#define REG_PKT_RSSI_VALUE          0x1A
#define REG_MODEM_CONFIG_1          0x1D
#define REG_MODEM_CONFIG_2          0x1E
#define REG_PREAMBLE_MSB            0x20
#define REG_PREAMBLE_LSB            0x21
#define REG_PAYLOAD_LENGTH          0x22
#define REG_MODEM_CONFIG_3          0x26
#define REG_SYNC_WORD               0x39
#define REG_DIO_MAPPING_1           0x40
#define REG_VERSION                 0x42
#define REG_PA_DAC                  0x4D

// Chế độ hoạt động OP_MODE
#define MODE_LONG_RANGE_MODE        0x80
#define MODE_SLEEP                  0x00
#define MODE_STDBY                  0x01
#define MODE_TX                     0x03
#define MODE_RXCONTINUOUS           0x05

// Cờ ngắt
#define IRQ_RXDONE_MASK             0x40
#define IRQ_PAYLOAD_CRC_ERROR_MASK  0x20

class SX1278_WiringPi {
public:
    SX1278_WiringPi(int csPin, int rstPin, int dio0Pin, double frequencyMHz);
    ~SX1278_WiringPi();

    bool begin();
    void reset();
    void setFrequency(double freqMHz);
    void setMode(uint8_t mode);
    bool isPacketAvailable();
    int readPacket(uint8_t* buffer, int maxLen, int& rssi, float& snr);
    bool sendPacket(const uint8_t* buffer, size_t len, uint32_t timeoutMs = 1000);

    static bool configureSpiNoCs();

    double getFrequency() const { return m_frequency; }
    int getCsPin() const { return m_csPin; }

private:
    uint8_t readRegister(uint8_t address);
    void writeRegister(uint8_t address, uint8_t value);
    void burstRead(uint8_t address, uint8_t* buffer, uint8_t len);
    void burstWrite(uint8_t address, const uint8_t* buffer, uint8_t len);

    static std::recursive_mutex s_spiMutex;

    int m_csPin;
    int m_rstPin;
    int m_dio0Pin;
    double m_frequency;
};

#endif // SX1278_WIRINGPI_H
