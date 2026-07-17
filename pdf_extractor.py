# -*- coding: utf-8 -*-
"""
แปลงราคาข้อมูลดาวเทียมจาก Gistda_Price_List.pdf เป็น CSV / XLSX / HTML
ข้อมูลราคาถูกจัดโครงสร้างเอง (ไม่ใช้ตารางดิบจาก PDF) เพราะแต่ละหน้าใน PDF
มีคอลัมน์ไม่ตรงกัน (Standard Archive/Tasking, Polarization, New Acquisition ฯลฯ)
และมีเซลล์รวม (merged cell) ปนอยู่ ทำให้ extract_tables() ตรงๆ ได้ผลลัพธ์ที่รก
ผลลัพธ์เป็นตารางเดียว (flat table) แถวละ 1 สินค้า/โหมด
"""

import csv
import pandas as pd

COLUMNS = [
    "กลุ่มข้อมูล", "ดาวเทียม/Mode", "รายละเอียดภาพ", "Polarization",
    "ประเภทราคาที่ 1", "ราคาที่ 1", "ประเภทราคาที่ 2", "ราคาที่ 2",
    "หน่วย", "หมายเหตุ",
]

ARCHIVE, TASKING = "ข้อมูลในคลัง (Standard Archive)", "ข้อมูลสั่งถ่าย (Standard Tasking)"

DISCLAIMER_LINE1 = "**ราคาดังกล่าวยังไม่รวมภาษีมูลค่าเพิ่ม"
DISCLAIMER_LINE2 = (
    "สอบถามรายละเอียดเพิ่มเติม: สำนักงานพัฒนาเทคโนโลยีอวกาศและภูมิสารสนเทศ (องค์การมหาชน) "
    "ฝ่ายพัฒนาธุรกิจและการบริการ โทร. 0 2143 9593, 0 2141 4564-66,69 อีเมล usd@gistda.or.th"
)
SOURCE_NOTE = "ที่มา: https://www.gistda.or.th/download/Gistda_Price_List.pdf"

# แต่ละแถว: (ดาวเทียม/Mode, รายละเอียดภาพ, Polarization,
#            ประเภทราคาที่ 1, ราคาที่ 1, ประเภทราคาที่ 2, ราคาที่ 2, หน่วย, หมายเหตุ)
CATEGORIES = [
    {
        "name": "ดาวเทียมรายละเอียดสูงมาก (30-50 cm)",
        "rows": [
            ("Pléiades NEO", "30 cm.", "", ARCHIVE, 880, TASKING, 1270, "บาท/ตร.กม.", ""),
            ("WorldView-4", "30 cm.", "", ARCHIVE, 920, TASKING, 1560, "บาท/ตร.กม.", ""),
            ("SuperView-2", "42 cm.", "", ARCHIVE, 700, TASKING, 1100, "บาท/ตร.กม.", ""),
            ("WorldView-1", "50 cm.", "", ARCHIVE, 700, TASKING, 1100, "บาท/ตร.กม.", ""),
            ("WorldView-2", "50 cm.", "", ARCHIVE, 700, TASKING, 1100, "บาท/ตร.กม.", ""),
            ("WorldView-3", "50 cm.", "", ARCHIVE, 700, TASKING, 1100, "บาท/ตร.กม.", ""),
            ("GeoEye-1", "50 cm.", "", ARCHIVE, 700, TASKING, 1100, "บาท/ตร.กม.", ""),
            ("Pléiades", "50 cm.", "", ARCHIVE, 490, TASKING, 830, "บาท/ตร.กม.", ""),
            ("EarthScanner", "50 cm.", "", ARCHIVE, 400, TASKING, 800, "บาท/ตร.กม.", ""),
            ("SuperView-1", "50 cm.", "", ARCHIVE, 500, TASKING, 900, "บาท/ตร.กม.", ""),
            ("KOMPSAT-3", "50 cm.", "", ARCHIVE, 400, TASKING, 700, "บาท/ตร.กม.", ""),
            ("SKYSAT", "50 cm.", "", ARCHIVE, 300, TASKING, 560, "บาท/ตร.กม.",
             "ข้อมูลในคลังพื้นที่สั่งขั้นต่ำ 1,250 ตร.กม. / ข้อมูลสั่งถ่ายโปรดติดต่อเจ้าหน้าที่ / "
             "เข้าดูผ่าน API/Explorer"),
        ],
    },
    {
        "name": "ดาวเทียมรายละเอียดสูง (60 cm - 2 m)",
        "rows": [
            ("QuickBird", "60 cm.", "", ARCHIVE, 700, TASKING, "N/A", "บาท/ตร.กม.", ""),
            ("GaoFen-7", "65 cm.", "", ARCHIVE, 400, TASKING, 700, "บาท/ตร.กม.", ""),
            ("Jilin", "75 cm.", "", ARCHIVE, 300, TASKING, 600, "บาท/ตร.กม.", ""),
            ("DailyVision", "75 cm.", "", ARCHIVE, 300, TASKING, 600, "บาท/ตร.กม.", ""),
            ("GaoFen-2", "80 cm.", "", ARCHIVE, 300, TASKING, 400, "บาท/ตร.กม.", ""),
            ("IKONOS", "1 m.", "", ARCHIVE, 400, TASKING, "N/A", "บาท/ตร.กม.", ""),
            ("SPOT-6", "1.5 m.", "", ARCHIVE, 190, TASKING, 230, "บาท/ตร.กม.", ""),
            ("SPOT-7", "1.5 m.", "", ARCHIVE, 190, TASKING, 230, "บาท/ตร.กม.", ""),
            ("ไทยโชต (Thaichote)", "2 m.", "", ARCHIVE, 700, TASKING, 6500, "บาท/ตร.กม.",
             "ราคาที่รับ Orthorectification แล้ว ราคา 910 บาท/ภาพ"),
            ("Video Constellation", "1 m.", "", ARCHIVE, 142500, TASKING, 285000, "บาท/30 วินาที",
             "ถ่ายภาพเคลื่อนไหวรูปแบบวิดีโอและภาพกลางคืน วิดีโอแต่ละช่วงจำกัดความยาว 30 วินาที"),
            ("Night Imaging", "1 m.", "", ARCHIVE, 800, TASKING, 1400, "บาท/ตร.กม.",
             "พื้นที่สั่งซื้อขั้นต่ำ (ในคลังและสั่งถ่ายใหม่) 100 ตร.กม. / "
             "ความกว้างแนวถ่ายภาพอย่างน้อย 5 กม."),
        ],
    },
    {
        "name": "ดาวเทียมรายละเอียดปานกลาง (> 2 m)",
        "rows": [
            ("LANDSAT-5", "30 m.", "", ARCHIVE, 150, TASKING, "N/A", "บาท/ภาพ",
             "คิดเฉพาะค่าดำเนินการผลิตข้อมูลจากคลังข้อมูล / Level 1T มีทั้งหมด 7 Bands"),
            ("LANDSAT-7", "30 m.", "", ARCHIVE, 150, TASKING, "N/A", "บาท/ภาพ",
             "คิดเฉพาะค่าดำเนินการผลิตข้อมูลจากคลังข้อมูล / Level 1T มีทั้งหมด 8 Bands"),
            ("LANDSAT-8", "30 m.", "", ARCHIVE, 150, TASKING, "N/A", "บาท/ภาพ",
             "หากประสงค์ให้ สทอภ. ดำเนินการดาวน์โหลด คิดค่าดำเนินการ 150 บาท/ภาพ / "
             "Level 1T มีทั้งหมด 11 Bands"),
            ("LANDSAT-9", "30 m.", "", ARCHIVE, 150, TASKING, "N/A", "บาท/ภาพ",
             "หากประสงค์ให้ สทอภ. ดำเนินการดาวน์โหลด คิดค่าดำเนินการ 150 บาท/ภาพ / "
             "Level 1T มีทั้งหมด 11 Bands"),
            ("PLANETSCOPE (Access+Download)", "3 m.", "", "ข้อมูลในคลัง", 180,
             "การติดตาม (Monitoring)", 240, "บาท/ตร.กม./ปี",
             "พื้นที่การสั่งขั้นต่ำ 100 ตร.กม. / ระยะเวลาสัญญา 1 ปี / "
             "เข้าดูและดาวน์โหลดผ่าน Planet Explorer, Planet API, Desktop GIS"),
        ],
    },
    {
        "name": "ดาวเทียมระบบเรดาร์ - RADARSAT-2 (C band)",
        "rows": [
            ("Standard", "25 m.", "", "Single Look complex", 57600, "Path Image", 57600, "บาท/ภาพ", ""),
            ("Spotlight A", "1 m.", "", "Single Look complex", 134400, "Path Image", 134400, "บาท/ภาพ", ""),
            ("Utra-Fine", "3 m.", "", "Single Look complex", 86400, "Path Image", 86400, "บาท/ภาพ", ""),
            ("Wide Utra-Fine", "3 m.", "", "Single Look complex", 124800, "Path Image", 124800, "บาท/ภาพ", ""),
            ("Multi-Look Fine", "8 m.", "", "Single Look complex", 67200, "Path Image", 67200, "บาท/ภาพ", ""),
            ("Wide Multi-Look Fine", "8 m.", "", "Single Look complex", 120000, "Path Image", 120000, "บาท/ภาพ", ""),
            ("Fine", "8 m.", "", "Single Look complex", 57600, "Path Image", 57600, "บาท/ภาพ", ""),
            ("Wide", "30 m.", "", "Single Look complex", 57600, "Path Image", 57600, "บาท/ภาพ", ""),
            ("ScanSAR Narrow", "50 m.", "", "Single Look complex", "N/A", "Path Image", 57600, "บาท/ภาพ", ""),
            ("ScanSAR Wide", "100 m.", "", "Single Look complex", "N/A", "Path Image", 57600, "บาท/ภาพ", ""),
            ("Extended High, Low", "25 m.", "", "Single Look complex", 57600, "Path Image", 57600, "บาท/ภาพ", ""),
            ("Fine Quad-Pol", "8 m.", "", "Single Look complex", 86400, "Path Image", "N/A", "บาท/ภาพ", ""),
            ("Wide Fine Quad-Pol", "8 m.", "", "Single Look complex", 124800, "Path Image", "N/A", "บาท/ภาพ", ""),
        ],
    },
    {
        "name": "ดาวเทียมระบบเรดาร์ - TerraSAR-X (X band)",
        "rows": [
            ("Staring Spotlight (ST)", "0.25 m.", "", ARCHIVE, 162630, TASKING, 325260, "บาท/ภาพ", ""),
            ("High Res Spotlight (HS)", "1 m.", "", ARCHIVE, 139230, TASKING, 278460, "บาท/ภาพ", ""),
            ("Spotlight", "2 m.", "", ARCHIVE, 99450, TASKING, 198900, "บาท/ภาพ", ""),
            ("StripMap", "3 m.", "", ARCHIVE, 69030, TASKING, 138060, "บาท/ภาพ", ""),
            ("ScanSAR", "18.5 m.", "", ARCHIVE, 40950, TASKING, 81900, "บาท/ภาพ", ""),
            ("Wide ScanSAR", "40 m.", "", ARCHIVE, 40950, TASKING, 81900, "บาท/ภาพ", ""),
        ],
    },
    {
        "name": "ดาวเทียมระบบเรดาร์ - COSMO SkyMed (X band)",
        "rows": [
            ("Spotlight-2", "1 x 1 m.", "HH, VV", "", "", "New Acquisition", 180000, "บาท/ภาพ", ""),
            ("StripMap Himage", "3x3 - 5x5 m.", "HH, HV, VH, VV", "", "", "New Acquisition", 93000, "บาท/ภาพ", ""),
            ("StripMap PingPong", "10x12 - 20x20 m.",
             "2 ช่องสัญญาณ polarimetric: HH,VV หรือ HH,HV หรือ VV,VH",
             "", "", "New Acquisition", 68000, "บาท/ภาพ", ""),
            ("ScanSAR Wide", "14x22 - 30x30 m.", "HH, HV, VH, VV", "", "", "New Acquisition", 78000, "บาท/ภาพ", ""),
            ("ScanSAR Huge", "14x38 - 100x100 m.", "HH, HV, VH, VV", "", "", "New Acquisition", 78000, "บาท/ภาพ", ""),
        ],
    },
    {
        "name": "ดาวเทียมระบบเรดาร์ - GaoFen-3 (C band)",
        "rows": [
            ("Spotlight (SL)", "1 m.", "HH, VV", ARCHIVE, 116400, TASKING, 180500, "บาท/ภาพ", ""),
            ("Ultra-fine Stripmap (UFS)", "3 m.", "HH, VV", ARCHIVE, 68900, TASKING, 118800, "บาท/ภาพ", ""),
            ("Fine Stripmap (FSI)", "5 m.", "HH, VV", ARCHIVE, 64200, TASKING, 95000, "บาท/ภาพ", ""),
            ("Wide Fine Stripmap (FSII)", "10 m.", "HH, HV / VV, VH", ARCHIVE, 64200, TASKING, 90300, "บาท/ภาพ", ""),
            ("Standard Stripmap (SS)", "25 m.", "HH, HV / VV, VH", ARCHIVE, 54700, TASKING, 85500, "บาท/ภาพ", ""),
            ("Narrow ScanSAR (NSC)", "50 m.", "HH, HV / VV, VH", ARCHIVE, 32100, TASKING, 42800, "บาท/ภาพ", ""),
            ("Wide ScanSAR (WSC)", "100 m.", "HH, HV / VV, VH", ARCHIVE, 32100, TASKING, 45800, "บาท/ภาพ", ""),
            ("Quad-pol Stripmap (QPSI)", "8 m.", "HH, HV / VV, VH", ARCHIVE, 71300, TASKING, 137800, "บาท/ภาพ", ""),
            ("Wide Quad-pol Stripmap (QPSII)", "25 m.", "HH, HV / VV, VH", ARCHIVE, 71300, TASKING, 137800, "บาท/ภาพ", ""),
            ("Wave (WAV)", "10 m.", "HH, HV / VV, VH", ARCHIVE, 10700, TASKING, 14300, "บาท/ภาพ", ""),
            ("Global Observation (GLO)", "500 m.", "HH, HV / VV, VH", ARCHIVE, 10700, TASKING, 14300, "บาท/ภาพ", ""),
            ("Extended Incidence Angle (EXT)", "25 m.", "HH, HV / VV, VH", ARCHIVE, 42800, TASKING, 57000, "บาท/ภาพ", ""),
        ],
    },
]


def build_dataframe():
    data = [
        (cat["name"],) + row
        for cat in CATEGORIES
        for row in cat["rows"]
    ]
    return pd.DataFrame(data, columns=COLUMNS)


def footer_rows(n_cols):
    pad = [""] * (n_cols - 1)
    return [[DISCLAIMER_LINE1] + pad, [DISCLAIMER_LINE2] + pad, [SOURCE_NOTE] + pad]


def export_csv(df, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        df.to_csv(f, index=False)
        writer = csv.writer(f)
        writer.writerows(footer_rows(len(df.columns)))


def export_xlsx(df, path):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Price List", index=False)
        ws = writer.sheets["Price List"]
        start = len(df) + 2
        for offset, row in enumerate(footer_rows(len(df.columns))):
            ws.cell(row=start + offset, column=1, value=row[0])


def export_html(df, path):
    parts = [
        "<html><head><meta charset='utf-8'>",
        "<title>GISTDA Satellite Price List</title>",
        "<style>",
        "body{font-family:Tahoma,Arial,sans-serif;margin:2rem;}",
        "h1{font-size:1.4rem;}",
        "table{border-collapse:collapse;width:100%;}",
        "th,td{border:1px solid #ccc;padding:6px 10px;text-align:left;font-size:0.85rem;}",
        "th{background:#f0f0f0;}",
        "p.footer{font-size:0.85rem;color:#555;}",
        "</style></head><body>",
        "<h1>ราคาข้อมูลจากดาวเทียม - GISTDA Satellite Price List</h1>",
        df.to_html(index=False, escape=True),
        f"<p class='footer'>{DISCLAIMER_LINE1}</p>",
        f"<p class='footer'>{DISCLAIMER_LINE2}</p>",
        f"<p class='footer'>{SOURCE_NOTE}</p>",
        "</body></html>",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def main():
    df = build_dataframe()
    export_csv(df, "Gistda_Price_List.csv")
    export_xlsx(df, "Gistda_Price_List.xlsx")
    export_html(df, "Gistda_Price_List.html")
    print("สร้างไฟล์สำเร็จ: Gistda_Price_List.csv, .xlsx, .html")


if __name__ == "__main__":
    main()
