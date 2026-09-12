# 📖 `m03_health_supp_db` CLI 工具使用說明手冊

* **模組代號**：`M03`
* **資料庫名稱**：`m03_health_supp_db`
* **描述**：台灣衛福部審查通過之健字號健康食品資料庫
* **最後更新**：2026-08-16

---

## 🎯 1. 功能與指令總覽

M03 模組收錄台灣所有獲頒健字號認證之健康食品名冊、功效宣稱與主要成分，並支援與 M01 處方藥物之交互作用檢索。

---

## ⚙️ 2. CLI 命令說明

### 建置資料庫 (`build`)
```bash
PYTHONPATH=. python src/cli/main.py m03 build --sample /Volumes/D2024/data/med-db-in/raw/tfda_health_food_full.json
```

### 檢索健康食品 (`search`)
```bash
PYTHONPATH=. python src/cli/main.py m03 search "紅麴"
```
