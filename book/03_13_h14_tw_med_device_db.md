# 專章 3.13：`M13 tw-med-device-db` 醫療器材許可證與說明書庫白皮書

* **模組代號**：`M13` (`tw_med_device_db`)
* **資料來源**：衛福部食品藥物管理署 (TFDA) 《醫療器材許可證與說明書/包裝資料集》
* **實體庫規模**：**66,459 筆全量醫療器材許可證** (含官方 PDF 說明書網址)

---

## 🏛️ 1. 模組架構與領域定位

`M13 tw-med-device-db` 收錄全台血壓計、血糖機、高階輔具與醫療器材許可證，解決臨床與醫藥檢索中「無法查驗醫器合規性與說明書」的痛點。

---

## 📊 2. 實體 Schema 與 5 大進階設計 (E1~E5)

1. **核心 Schema**：`licence_id` (PK), `device_name_c`, `device_name_e`, `applicant_name`, `manufacturer_name`, `validity_date`, `category_code`, `manual_url`, `attributes_json` (剛性 `_v: 1.0.0`)。
2. **E1 HL7 FHIR R4 Device Resource 轉譯**：轉譯實體為國際標準 FHIR `Device` / `DeviceDefinition` JSON。
3. **E2 同級平價替代品圖譜**：`m13 substitutes` 自動比對相同分類等級 (`category_code`) 與適應症之替代器材。

---

## ⚙️ 3. 實務 CLI 操作範例

```bash
# 1. 關鍵字搜尋醫療器材
python src/cli/main.py m13 search "血壓計" --db db/med.db

# 2. 同級同適應症平價替代品比對
python src/cli/main.py m13 substitutes 內衛成製字第000012號 --db db/med.db
```
