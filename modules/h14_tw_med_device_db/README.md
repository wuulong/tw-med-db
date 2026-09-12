# 🩺 `M13 tw-med-device-db` (醫療器材許可證與說明書庫)

* **模組代號**：`M13`
* **資料來源**：衛福部食藥署 (TFDA) 《醫療器材許可證與說明書/包裝資料集》
* **核心表名**：`m13_tw_med_device_db`
* **主要功能**：收錄全台醫療器材許可證、廠商、有效日期與官方說明書 PDF 下載連結。

## ⚙️ CLI 指令簡介
```bash
python src/cli/main.py m13 search "血壓計" --db db/med.db
python src/cli/main.py m13 substitutes --licence-id "衛部醫器輸字第030001號"
```
