#include "sx1278_wiringpi.h"
#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#define SPI_CHANNEL 0

SX1278_WiringPi::SX1278_WiringPi(int csPin, int rstPin, int dio0Pin, double frequencyMHz)
    : m_csPin(csPin), m_rstPin(rstPin), m_dio0Pin(dio0Pin), m_frequency(frequencyMHz) {}

SX1278_WiringPi::~SX1278_WiringPi() {
    setMode(MODE_SLEEP);
}

void SX1278_WiringPi::writeRegister(uint8_t address, uint8_t value) {
    uint8_t tx[2] = { (uint8_t)(address | 0x80), value };
    digitalWrite(m_csPin, LOW);
    wiringPiSPIDataRW(SPI_CHANNEL, tx, 2);
    digitalWrite(m_csPin, HIGH);
}

uint8_t SX1278_WiringPi::readRegister(uint8_t address) {
    uint8_t tx[2] = { (uint8_t)(address & 0x7F), 0x00 };
    digitalWrite(m_csPin, LOW);
    wiringPiSPIDataRW(SPI_CHANNEL, tx, 2);
    digitalWrite(m_csPin, HIGH);
    return tx[1];
}

void SX1278_WiringPi::burstRead(uint8_t address, uint8_t* buffer, uint8_t len) {
    uint8_t tx[256];
    tx[0] = address & 0x7F;
    memset(tx + 1, 0, len);
    digitalWrite(m_csPin, LOW);
    wiringPiSPIDataRW(SPI_CHANNEL, tx, len + 1);
    digitalWrite(m_csPin, HIGH);
    memcpy(buffer, tx + 1, len);
}

void SX1278_WiringPi::reset() {
    digitalWrite(m_rstPin, LOW);
    delay(10);
    digitalWrite(m_rstPin, HIGH);
    delay(10);
}

void SX1278_WiringPi::setMode(uint8_t mode) {
    writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | mode);
}

void SX1278_WiringPi::setFrequency(double freqMHz) {
    m_frequency = freqMHz;
    uint64_t frf = ((uint64_t)freqMHz * 1000000) / 61.03515625;
    writeRegister(REG_FRF_MSB, (uint8_t)((frf >> 16) & 0xFF));
    writeRegister(REG_FRF_MID, (uint8_t)((frf >> 8) & 0xFF));
    writeRegister(REG_FRF_LSB, (uint8_t)(frf & 0xFF));
}

bool SX1278_WiringPi::begin() {
    pinMode(m_csPin, OUTPUT);
    digitalWrite(m_csPin, HIGH);

    pinMode(m_rstPin, OUTPUT);
    pinMode(m_dio0Pin, INPUT);

    reset();

    // Kiểm tra chip version (SX1278 thường trả về 0x12)
    uint8_t version = readRegister(REG_VERSION);
    if (version != 0x12) {
        printf("[WARN CS:%d] Silicon version 0x%02X (expected 0x12)\n", m_csPin, version);
    }

    // Đưa về chế độ Sleep rồi chuyển sang LoRa Mode
    writeRegister(REG_OP_MODE, MODE_SLEEP);
    delay(10);
    writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_SLEEP);
    delay(10);

    // Cấu hình tần số
    setFrequency(m_frequency);

    // Cấu hình LoRa: BW=125kHz, CR=4/5 (0x72), SF=7 (0x74), Preamble=8, SyncWord=0x12
    writeRegister(REG_MODEM_CONFIG_1, 0x72); // BW 125kHz, CR 4/5, Explicit header
    writeRegister(REG_MODEM_CONFIG_2, 0x74); // SF7, CRC enable
    writeRegister(REG_MODEM_CONFIG_3, 0x04); // LowDataRateOptimize off, AGC Auto on
    writeRegister(REG_SYNC_WORD, 0x12);      // Private sync word

    // Preamble length 8
    writeRegister(REG_PREAMBLE_MSB, 0x00);
    writeRegister(REG_PREAMBLE_LSB, 0x08);

    // Base address FIFO RX = 0
    writeRegister(REG_FIFO_RX_BASE_ADDR, 0x00);
    writeRegister(REG_FIFO_ADDR_PTR, 0x00);

    // Bật chế độ liên tục nhận (RX Continuous)
    setMode(MODE_RXCONTINUOUS);
    return true;
}

bool SX1278_WiringPi::isPacketAvailable() {
    // Kiểm tra chân DIO0 (HIGH khi có gói) hoặc thanh ghi IRQ_FLAGS
    if (digitalRead(m_dio0Pin) == HIGH) {
        return true;
    }
    uint8_t irq = readRegister(REG_IRQ_FLAGS);
    return (irq & IRQ_RXDONE_MASK) != 0;
}

int SX1278_WiringPi::readPacket(uint8_t* buffer, int maxLen, int& rssi, float& snr) {
    uint8_t irqFlags = readRegister(REG_IRQ_FLAGS);

    // Xóa cờ ngắt
    writeRegister(REG_IRQ_FLAGS, irqFlags);

    // Kiểm tra lỗi CRC
    if (irqFlags & IRQ_PAYLOAD_CRC_ERROR_MASK) {
        return -1; // CRC Error
    }

    if (!(irqFlags & IRQ_RXDONE_MASK)) {
        return 0; // Chưa nhận xong
    }

    // Đọc số byte nhận được
    int nbBytes = readRegister(REG_RX_NB_BYTES);
    if (nbBytes > maxLen) nbBytes = maxLen;

    // Đặt con trỏ FIFO về vị trí bắt đầu gói hiện tại
    uint8_t currentAddr = readRegister(REG_FIFO_RX_CURRENT_ADDR);
    writeRegister(REG_FIFO_ADDR_PTR, currentAddr);

    // Đọc payload từ FIFO
    burstRead(REG_FIFO, buffer, nbBytes);

    // Tính toán RSSI và SNR (Dải 433 MHz < 525 MHz: RSSI offset = -164)
    int rawRssi = readRegister(REG_PKT_RSSI_VALUE);
    rssi = -164 + rawRssi;

    int8_t rawSnr = (int8_t)readRegister(REG_PKT_SNR_VALUE);
    snr = rawSnr * 0.25f;

    // Đưa lại về RX Continuous
    setMode(MODE_RXCONTINUOUS);
    return nbBytes;
}
