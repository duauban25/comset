from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg
import pandas as pd
import os, sys
import tempfile

# =========================================================
# RESOURCE PATH (agar logo tetap ditemukan setelah dibundle)
# =========================================================
def resource_path(relative_path):
    """Ambil path absolut ke file, baik saat dijalankan normal atau hasil bundle .exe/.app"""
    try:
        base_path = sys._MEIPASS  # Folder temporer PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# =========================================================
# MAIN FUNCTION
# =========================================================
def generate_pdf_report(summary_data, selected_date, logo_path=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30, bottomMargin=30)
    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterBold', alignment=1, fontSize=14, leading=16, spaceAfter=10))
    styles.add(ParagraphStyle(name='TableHeader', alignment=1, fontSize=10, leading=12, textColor=colors.white))
    styles.add(ParagraphStyle(name='TableCell', alignment=1, fontSize=9, leading=10))

    # =========================================================
    # HEADER SECTION
    # =========================================================
    try:
        if logo_path:
            logo_full = logo_path if os.path.isabs(logo_path) else resource_path(logo_path)
            if os.path.exists(logo_full):
                elements.append(Image(logo_full, width=200, height=80))
                elements.append(Spacer(1, 6))
    except Exception as e:
        print(f"⚠️ Logo gagal dimuat: {e}")

    elements.append(Paragraph("Comparative Statistic Report", styles['CenterBold']))
    elements.append(Paragraph(f"Date: {selected_date.strftime('%d %B %Y')}", styles['CenterBold']))
    elements.append(Spacer(1, 12))

    # =========================================================
    # TABLE GENERATION FUNCTION
    # =========================================================
    def build_table(df, title):
        data = [list(df.columns)] + df.values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2EC4B6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f7f7')]),
        ]))
        elements.append(Paragraph(f"<b>{title}</b>", styles['CenterBold']))
        elements.append(table)
        elements.append(Spacer(1, 12))

    # =========================================================
    # GENERATE TABLES FOR EACH PERIOD
    # =========================================================
    for title, df in summary_data.items():
        if df.empty:
            continue
        df_display = df.copy()

        # Format angka agar rapi
        for col in ['Room_Available', 'Room_Sold']:
            if col in df_display.columns:
                df_display[col] = df_display[col].map('{:,.0f}'.format)
        for col in ['Revenue', 'ADR', 'ARR', 'RevPAR']:
            if col in df_display.columns:
                df_display[col] = df_display[col].map('Rp {:,.0f}'.format)
        for col in ['Occ%']:
            if col in df_display.columns:
                df_display[col] = df_display[col].map('{:,.2f}%'.format)
        for col in ['RGI', 'MPI', 'ARI']:
            if col in df_display.columns:
                df_display[col] = df_display[col].map('{:,.2f}'.format)
        for col in ['Fair_Share']:
            if col in df_display.columns:
                df_display[col] = df_display[col].map('{:,.2%}'.format)
        if 'Rank' in df_display.columns:
            df_display['Rank'] = df_display['Rank'].fillna('').astype(str)

        build_table(df_display, title.replace("_", " "))

    # =========================================================
    # ADD GRAPH (RevPAR Comparison)
    # =========================================================
    try:
        first_df = next(iter(summary_data.values()))
        if not first_df.empty and 'RevPAR' in first_df.columns:
            df = first_df.copy()

            # Pastikan index berisi nama hotel
            if 'Hotel' in df.columns:
                df.set_index('Hotel', inplace=True)

            hotels = df.index.tolist()
            if 'TOTAL' in hotels:
                hotels.remove('TOTAL')

            values = df.loc[hotels, 'RevPAR']
            total_value = df.loc['TOTAL', 'RevPAR'] if 'TOTAL' in df.index else values.mean()

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(hotels, values, color='#2EC4B6', alpha=0.8, label='Hotels')
            ax.plot(hotels, [total_value]*len(hotels), color='red', linestyle='--', linewidth=2, label='Total')
            ax.set_title("RevPAR Comparison: Hotels vs Total", fontsize=12)
            ax.set_xlabel("Hotels")
            ax.set_ylabel("RevPAR (Rp)")
            ax.legend()
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            img_buf = BytesIO()
            plt.savefig(img_buf, format='png', dpi=150)
            plt.close(fig)
            img_buf.seek(0)

            elements.append(Spacer(1, 20))
            elements.append(Paragraph("<b>Overall Graphic Summary (RevPAR)</b>", styles['CenterBold']))
            elements.append(Spacer(1, 8))
            elements.append(Image(img_buf, width=600, height=250))
    except Exception as e:
        print(f"⚠️ Error generating chart: {e}")

    # =========================================================
    # BUILD PDF
    # =========================================================
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ===============================================
# generate_graphic_pdf(summary)
# ===============================================
from fpdf import FPDF
import os
from datetime import datetime

def generate_graphic_pdf(summary_df, report_date=None, logo_path=None):
    try:
        # Pastikan folder tujuan ada dan bisa ditulis (Downloads)
        output_folder = os.path.expanduser("~/Downloads")
        os.makedirs(output_folder, exist_ok=True)

        # Buat nama file unik
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.join(output_folder, f"graphic_report_{timestamp}.pdf")

        # Siapkan data
        df = summary_df.fillna(0).copy()
        hotels = df.get("Hotel", pd.Series([f"H{i+1}" for i in range(len(df))])).tolist()

        printed_at = datetime.now()

        # Resolve logo path if not provided
        if not logo_path:
            candidate = resource_path("Daun_logo.jpg")
            logo_candidate = candidate if os.path.exists(candidate) else None
        else:
            logo_candidate = logo_path if os.path.exists(logo_path) else None

        def add_header_footer(fig, title, page_no):
            # Margins and header/footer texts (wider margins for better visual balance)
            # left/right/top/bottom are fractions of figure from 0..1
            fig.subplots_adjust(left=0.14, right=0.86, top=0.76, bottom=0.18)
            header_title = "Comparative Graphic Report"
            header_right = f"Report Date: {report_date.strftime('%d %b %Y') if report_date else '-'}"
            footer_left = f"Printed: {printed_at.strftime('%d %b %Y %H:%M:%S')}"
            footer_right = f"Page {page_no}"
            # Header area with centered logo + title
            if logo_candidate:
                try:
                    img = mpimg.imread(logo_candidate)
                    # x, y, w, h in figure coords; place near top center
                    ax_logo = fig.add_axes([0.43, 0.90, 0.14, 0.07])
                    ax_logo.imshow(img)
                    ax_logo.axis('off')
                except Exception:
                    pass
            fig.text(0.5, 0.885, header_title, fontsize=12, fontweight='bold', ha='center', va='top')
            fig.text(0.99, 0.885, header_right, fontsize=10, ha='right', va='top')
            fig.text(0.01, 0.10, footer_left, fontsize=9, ha='left', va='bottom')
            fig.text(0.99, 0.10, footer_right, fontsize=9, ha='right', va='bottom')

        cmap = plt.get_cmap('tab10')
        special_colors = {
            "Daun Bali Seminyak": "#10B981",  # emerald/green
            "Daun Bali Seminyak Hotel": "#10B981",
            "Kamania Hotel Petitenget": "#EF4444",  # red
            "Kamanya Petitenget": "#EF4444",
        }
        def _color_for(h):
            return special_colors.get(h, cmap((hotels.index(h)) % 10))
        bar_colors = [_color_for(h) for h in hotels]

        page_no = 1
        with PdfPages(pdf_path) as pdf:
            # 1) Occupancy chart + garis compset
            try:
                compset_occ = 0.0
                if df["Room_Available"].sum() > 0:
                    compset_occ = (df["Room_Sold"].sum() / df["Room_Available"].sum()) * 100.0
                fig, ax = plt.subplots(figsize=(11.7, 8.3))  # A4 landscape-ish in inches
                ax.bar(hotels, df.get("Occupancy", 0.0), color=bar_colors)
                ax.axhline(compset_occ, color="red", linestyle="--", linewidth=2, label=f"Compset {compset_occ:.1f}%")
                ax.set_title("Occupancy vs Compset", fontsize=14)
                ax.set_ylabel("Occupancy (%)")
                ax.legend()
                plt.xticks(rotation=45, ha='right')
                add_header_footer(fig, "Occupancy vs Compset", page_no)
                pdf.savefig(fig)
                plt.close(fig)
                page_no += 1
            except Exception:
                pass

            # 2) Revenue chart + garis rata-rata per hotel
            try:
                avg_rev = float(df.get("Room_Revenue", 0.0).sum()) / max(len(df), 1)
                fig, ax = plt.subplots(figsize=(11.7, 8.3))
                ax.bar(hotels, df.get("Room_Revenue", 0.0), color=bar_colors)
                ax.axhline(avg_rev, color="red", linestyle="--", linewidth=2, label=f"Avg {avg_rev:,.0f}")
                ax.set_title("Revenue vs Compset Average", fontsize=14)
                ax.set_ylabel("Revenue (IDR)")
                ax.legend()
                plt.xticks(rotation=45, ha='right')
                add_header_footer(fig, "Revenue vs Compset Average", page_no)
                pdf.savefig(fig)
                plt.close(fig)
                page_no += 1
            except Exception:
                pass

            # 3) Index charts (MPI, ARI, RGI) + garis 100
            try:
                for idx_name, color in [("MPI", "#6366F1"), ("ARI", "#F59E0B"), ("RGI", "#EF4444")]:
                    if idx_name in df.columns:
                        fig, ax = plt.subplots(figsize=(11.7, 8.3))
                        ax.bar(hotels, df[idx_name], color=bar_colors)
                        ax.axhline(100.0, color="red", linestyle="--", linewidth=2, label="Benchmark 100")
                        ax.set_title(f"{idx_name} (100 = Benchmark)", fontsize=14)
                        ax.set_ylabel("Index")
                        ax.legend()
                        plt.xticks(rotation=45, ha='right')
                        add_header_footer(fig, f"{idx_name} (100 = Benchmark)", page_no)
                        pdf.savefig(fig)
                        plt.close(fig)
                        page_no += 1
            except Exception:
                pass

            # 4) Market Fair Share + garis rata-rata 100/len
            try:
                if "Market_Fair_Share" in df.columns and len(df) > 0:
                    avg_fair = 100.0 / len(df)
                    fig, ax = plt.subplots(figsize=(11.7, 8.3))
                    ax.bar(hotels, df["Market_Fair_Share"], color=bar_colors)
                    ax.axhline(avg_fair, color="red", linestyle="--", linewidth=2, label=f"Avg {avg_fair:.1f}%")
                    ax.set_title("Market Fair Share (%)", fontsize=14)
                    ax.set_ylabel("%")
                    ax.legend()
                    plt.xticks(rotation=45, ha='right')
                    add_header_footer(fig, "Market Fair Share (%)", page_no)
                    pdf.savefig(fig)
                    plt.close(fig)
                    page_no += 1
            except Exception:
                pass

        return pdf_path

    except Exception as e:
        print("❌ Gagal membuat PDF alternatif:", e)
        import traceback
        traceback.print_exc()
        return None




