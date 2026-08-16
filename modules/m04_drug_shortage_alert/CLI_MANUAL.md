# 📖 `m04_drug_shortage_alert` CLI 工具使用說明手冊

* **模組代號**：`M04`
* **資料庫名稱**：`m04_recalls`
* **描述**：台灣 TFDA 藥品回收與缺藥通報警訊資料庫
* **最後更新**：2026-08-16

---

## 🎯 1. 功能與指令總覽

M04 模組收錄台灣藥品回收公告、批號、回收原因與缺藥通報資訊，提供即時臨床用藥安全警訊。

---

## ⚙️ 2. CLI 命令說明

### 建置資料庫 (`build`)
```bash
PYTHONPATH=. python src/cli/main.py m04 build --sample /Volumes/D2024/data/med-db-in/raw/tfda_recalls_full.json
```

### 檢索回收警訊 (`search`)
```bash
PYTHONPATH=. python src/cli/main.py m04 search "回收"
```
