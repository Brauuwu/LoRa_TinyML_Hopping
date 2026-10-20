#ifndef CONFIG_H
#define CONFIG_H

// ═══════════════════════════════════════════════════════════════════════════
// CẤU HÌNH PHẦN CỨNG GATEWAY: RASPBERRY PI CM4 + 3 MODULE RA-02 (SX1278)
// Sử dụng thư viện WiringPi (chân đánh số theo WiringPi pinout)
// ═══════════════════════════════════════════════════════════════════════════

// ── SPI Bus cấu hình chung (SPI0 trên CM4) ──────────────────────────────────
#define SPI_CHANNEL         0         // /dev/spidev0.x
#define SPI_SPEED           2000000   // 2 MHz

// ── Sơ đồ chân WiringPi cho 3 Module Ra-02 ──────────────────────────────────
// Chú thích: BCM GPIO -> WiringPi Pin tương ứng trên Raspberry Pi 40-pin header

// Module 1 (Kênh 1: 433.175 MHz)
#define MODULE1_CS_PIN      10        // BCM GPIO 8  (CE0)
#define MODULE1_RST_PIN      2        // BCM GPIO 27
#define MODULE1_DIO0_PIN     3        // BCM GPIO 22
#define MODULE1_FREQ        433.175

// Module 2 (Kênh 2: 433.375 MHz)
#define MODULE2_CS_PIN      11        // BCM GPIO 7  (CE1)
#define MODULE2_RST_PIN      0        // BCM GPIO 17
#define MODULE2_DIO0_PIN     1        // BCM GPIO 18
#define MODULE2_FREQ        433.375

// Module 3 (Kênh 3: 433.575 MHz)
#define MODULE3_CS_PIN       6        // BCM GPIO 25 (Software CS)
#define MODULE3_RST_PIN      5        // BCM GPIO 24
#define MODULE3_DIO0_PIN     4        // BCM GPIO 23
#define MODULE3_FREQ        433.575

// ── Thông số RF LoRa tiêu chuẩn ─────────────────────────────────────────────
#define LORA_BW_KHZ         125.0
#define LORA_SF             7
#define LORA_CR             5         // 4/5
#define LORA_SYNC_WORD      0x12      // Private Sync Word
#define LORA_PREAMBLE_LEN   8

#endif // CONFIG_H
