#include "sx1278_wiringpi.h"
#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>

#ifndef SPI_NO_CS
#define SPI_NO_CS 0x40
#endif

#define SPI_CHANNEL 0

std::recursive_mutex SX1278_WiringPi::s_spiMutex;

bool SX1278_WiringPi::configureSpiNoCs() {
    int fd = wiringPiSPIGetFd(SPI_CHANNEL);
    if (fd < 0) {
        fprintf(stderr, "[WARN] Không thể lấy file descriptor của SPI0!\n");
        return false;
    }
    uint8_t mode = 0;
    if (ioctl(fd, SPI_IOC_RD_MODE, &mode) < 0) {
        perror("[WARN] Không đọc được SPI mode");
        return false;
    }
    mode |= SPI_NO_CS;
    if (ioctl(fd, SPI_IOC_WR_MODE, &mode) < 0) {
        perror("[WARN] Không đặt được SPI_NO_CS");
        return false;
    }
    printf("[SPI] Đã kích hoạt SPI_NO_CS (Kernel không tự động can thiệp chân CS phần cứng).\n");
    return true;
}

SX1278_WiringPi::SX1278_WiringPi(int csPin, int rstPin, int dio0Pin, double frequencyMHz)
    : m_csPin(csPin), m_rstPin(rstPin), m_dio0Pin(dio0Pin), m_frequency(frequencyMHz) {}

SX1278_WiringPi::~SX1278_WiringPi() {
    setMode(MODE_SLEEP);
}

void SX1278_WiringPi::writeRegister(uint8_t address, uint8_t value) {
    std::lock_guard<std::recursive_mutex> lock(s_spiMutex);
    uint8_t tx[2] = { (uint8_t)(address | 0x80), value };
    digitalWrite(m_csPin, LOW);
    wiringPiSPIDataRW(SPI_CHANNEL, tx, 2);
    digitalWrite(m_csPin, HIGH);
}

uint8_t SX1278_WiringPi::readRegister(uint8_t address) {
    std::lock_guard<std::recursive_mutex> lock(s_spiMutex);
    uint8_t tx[2] = { (uint8_t)(address & 0x7F), 0x00 };
    digitalWrite(m_csPin, LOW);
    wiringPiSPIDataRW(SPI_CHANNEL, tx, 2);
    digitalWrite(m_csPin, HIGH);
    return tx[1];
}

void SX1278_WiringPi::burstRead(uint8_t address, uint8_t* buffer, uint8_t len) {
    std::lock_guard<std::recursive_mutex> lock(s_spiMutex);
    uint8_t tx[256];
    tx[0] = address & 0x7F;
    memset(tx + 1, 0, len);
    digitalWrite(m_csPin, LOW);
    wiringPiSPIDataRW(SPI_CHANNEL, tx, len + 1);
    digitalWrite(m_csPin, HIGH);
    memcpy(buffer, tx + 1, len);
}

void SX1278_WiringPi::reset() {
    std::lock_guard<std::recursive_mutex> lock(s_spiMutex);
    digitalWrite(m_rstPin, LOW);
    delay(10);
    digitalWrite(m_rstPin, HIGH);
    delay(10);
}

void SX1278_WiringPi::setMode(uint8_t mode) {
    std::lock_guard<std::recursive_mutex> lock(s_spiMutex);
    writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | mode);
}

void SX1278_WiringPi::setFrequency(double freqMHz) {
    std::lock_guard<std::recursive_mutex> lock(s_spiMutex);
    m_frequency = freqMHz;
    uint32_t frf = (uint32_t)((freqMHz * 1000000.0) / 61.03515625);
    writeRegister(REG_FRF_MSB, (uint8_t)((frf >> 16) & 0xFF));
    writeRegister(REG_FRF_MID, (uint8_t)((frf >> 8) & 0xFF));
    writeRegister(REG_FRF_LSB, (uint8_t)(frf & 0xFF));
}

bool SX1278_WiringPi::begin() {
    std::lock_guard<std::recursive_mutex> lock(s_spiMutex);
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

    // Cấu hình công suất phát PA_BOOST (+17 dBm) cho module Ra-02 (SX1278)
    // Bit 7: PaSelect = 1 (kết nối antenna qua chân PA_BOOST pin 22), MaxPower = 7, OutputPower = 15 -> +17 dBm
    writeRegister(REG_PA_CONFIG, 0x8F);
    writeRegister(REG_PA_DAC, 0x84);

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

    // DIO0 mapping: 00 = RxDone
    writeRegister(REG_DIO_MAPPING_1, 0x00);

    // Xóa toàn bộ cờ ngắt cũ
    writeRegister(REG_IRQ_FLAGS, 0xFF);

    // Bật chế độ liên tục nhận (RX Continuous)
    setMode(MODE_RXCONTINUOUS);
    return true;
}

bool SX1278_WiringPi::isPacketAvailable() {
    // Chỉ kiểm tra chân ngắt DIO0 phần cứng (HIGH khi RxDone).
    // Tuyệt đối không thăm dò SPI khi DIO0=LOW để tránh chiếm bus và gây xung đột SPI giữa 3 module.
    return (digitalRead(m_dio0Pin) == HIGH);
}

int SX1278_WiringPi::readPacket(uint8_t* buffer, int maxLen, int& rssi, float& snr) {
    std::lock_guard<std::recursive_mutex> lock(s_spiMutex);
    uint8_t irqFlags = readRegister(REG_IRQ_FLAGS);

    // Xóa cờ ngắt
    writeRegister(REG_IRQ_FLAGS, 0xFF);

    // Kiểm tra lỗi CRC
    if (irqFlags & IRQ_PAYLOAD_CRC_ERROR_MASK) {
        setMode(MODE_RXCONTINUOUS);
        return -1; // CRC Error
    }

    if (!(irqFlags & IRQ_RXDONE_MASK)) {
        setMode(MODE_RXCONTINUOUS);
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

void SX1278_WiringPi::burstWrite(uint8_t address, const uint8_t* buffer, uint8_t len) {
    std::lock_guard<std::recursive_mutex> lock(s_spiMutex);
    uint8_t tx[256];
    tx[0] = address | 0x80;
    memcpy(tx + 1, buffer, len);
    digitalWrite(m_csPin, LOW);
    wiringPiSPIDataRW(SPI_CHANNEL, tx, len + 1);
    digitalWrite(m_csPin, HIGH);
}

bool SX1278_WiringPi::sendPacket(const uint8_t* buffer, size_t len, uint32_t timeoutMs) {
    if (len > 255) len = 255;
    std::lock_guard<std::recursive_mutex> lock(s_spiMutex);

    // 1. Chuyển sang chế độ Standby
    setMode(MODE_STDBY);

    // 2. Đảm bảo cấu hình công suất phát PA_BOOST (+17 dBm)
    writeRegister(REG_PA_CONFIG, 0x8F);
    writeRegister(REG_PA_DAC, 0x84);

    // 3. Đặt con trỏ FIFO về TX Base
    uint8_t txBase = readRegister(REG_FIFO_TX_BASE_ADDR);
    writeRegister(REG_FIFO_ADDR_PTR, txBase);

    // 4. Nạp dữ liệu vào FIFO
    burstWrite(REG_FIFO, buffer, (uint8_t)len);

    // 5. Thiết lập độ dài Payload
    writeRegister(REG_PAYLOAD_LENGTH, (uint8_t)len);

    // 6. Cấu hình DIO0: ngắt TxDone (bits 7:6 = 01 -> 0x40)
    writeRegister(REG_DIO_MAPPING_1, 0x40);

    // 7. Xóa cờ ngắt cũ
    writeRegister(REG_IRQ_FLAGS, 0xFF);

    // 8. Bật chế độ phát sóng TX
    setMode(MODE_TX);

    // 8. Chờ cờ TxDone (bit 3 của REG_IRQ_FLAGS = 0x08)
    uint32_t waited = 0;
    bool success = false;
    while (waited < timeoutMs) {
        uint8_t irq = readRegister(REG_IRQ_FLAGS);
        if (irq & 0x08) { // TxDone hoàn tất
            success = true;
            break;
        }
        usleep(2000); // 2ms
        waited += 2;
    }

    // 9. Xóa cờ ngắt
    writeRegister(REG_IRQ_FLAGS, 0xFF);

    // 10. Đặt lại DIO0 về RxDone (0x00)
    writeRegister(REG_DIO_MAPPING_1, 0x00);

    // 11. Chuyển lại về chế độ nhận liên tục
    setMode(MODE_RXCONTINUOUS);

    return success;
}
