import io

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image


st.set_page_config(
    page_title="Game Performance Analyzer",
    page_icon="🎮",
    layout="wide"
)

st.title("Game Performance Analyzer")
st.caption("Upload an MSI Afterburner log file and analyze performance metrics.")


def parse_optional_float(value):
    try:
        value = str(value).strip()
        if value in ["", "N/A", "NA", "-", "nan"]:
            return None
        return float(value)
    except Exception:
        return None


def normalize_metric_name(name):
    name = str(name).lower().strip()

    if "gpu temperature" in name:
        return "Temp"

    if "gpu usage" in name:
        return "GPU"

    if "cpu temperature" in name:
        return "CPU Temp"

    if "cpu usage" in name:
        return "CPU"

    if "framerate" in name and "min" not in name and "avg" not in name and "max" not in name and "low" not in name:
        return "FPS"

    if "frametime" in name or "frame time" in name:
        return "Frametime"

    return None


def parse_afterburner_log(file):
    """
    Parses MSI Afterburner logs using the header line instead of fixed column positions.

    This is important because the column order changes when you enable extra metrics.
    Example:
    GPU temperature, GPU usage, CPU temperature, CPU usage, Framerate, Frametime

    The old parser assumed:
    GPU temperature, GPU usage, CPU usage, Framerate
    so CPU temperature shifted everything and graphs became mixed.
    """
    rows = []
    current_columns = []

    for raw_line in file:
        line = raw_line.decode("latin-1", errors="ignore")
        parts = [p.strip() for p in line.split(",")]

        if len(parts) < 3:
            continue

        row_type = parts[0]

        # Metric header line
        if row_type == "02":
            current_columns = []

            for metric_name in parts[2:]:
                clean_name = normalize_metric_name(metric_name)

                if clean_name:
                    current_columns.append(clean_name)
                elif metric_name.strip() != "":
                    current_columns.append(None)

            continue

        # Real data line
        if row_type == "80" and current_columns:
            values = parts[2:2 + len(current_columns)]
            row = {}

            for column_name, value in zip(current_columns, values):
                if column_name is not None:
                    row[column_name] = parse_optional_float(value)

            if row:
                rows.append(row)

    df = pd.DataFrame(rows)

    expected_order = ["Temp", "GPU", "CPU Temp", "CPU", "FPS", "Frametime"]
    existing_columns = [col for col in expected_order if col in df.columns]
    df = df[existing_columns]

    # If MSI Afterburner does not export Frametime, calculate it from FPS.
    if "Frametime" not in df.columns and "FPS" in df.columns:
        df["Frametime"] = df["FPS"].apply(
            lambda x: 1000 / x if pd.notna(x) and x > 0 else None
        )

    # Clean empty rows and reset index for clean graphs.
    df = df.dropna(how="all").reset_index(drop=True)

    return df


def build_performance_chart(df):
    plt.style.use("dark_background")

    charts = [
        ("FPS", "Frame Rate (FPS)", "limegreen"),
        ("Frametime", "Frame Time (ms)", "orange"),
        ("CPU", "CPU Usage (%)", "dodgerblue"),
        ("GPU", "GPU Usage (%)", "purple"),
        ("Temp", "GPU Temperature (°C)", "red"),
        ("CPU Temp", "CPU Temperature (°C)", "cyan"),
    ]

    available_charts = [chart for chart in charts if chart[0] in df.columns]

    fig, ax = plt.subplots(
        len(available_charts),
        1,
        figsize=(12, max(10, len(available_charts) * 2.6))
    )

    if len(available_charts) == 1:
        ax = [ax]

    for current_ax, (column, title, color) in zip(ax, available_charts):
        current_ax.plot(df[column].reset_index(drop=True), color=color)
        current_ax.set_title(title)
        current_ax.set_xlabel("Sample")
        current_ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def build_top_spikes_table(spikes):
    if len(spikes) == 0:
        return pd.DataFrame()

    sort_columns = ["FPS"]
    ascending = [True]

    if "Frametime" in spikes.columns:
        sort_columns.append("Frametime")
        ascending.append(False)

    top_spikes = spikes.sort_values(
        by=sort_columns,
        ascending=ascending
    ).head(10)

    top_spikes_display = top_spikes.reset_index().rename(columns={
        "index": "Record",
        "FPS": "FPS at Drop",
        "Frametime": "Frame Time (ms)",
        "CPU": "CPU Usage (%)",
        "GPU": "GPU Usage (%)",
        "Temp": "GPU Temp (°C)",
        "CPU Temp": "CPU Temp (°C)"
    })

    columns_to_show = [
        "Record",
        "FPS at Drop",
        "Frame Time (ms)",
        "CPU Usage (%)",
        "GPU Usage (%)",
        "GPU Temp (°C)",
        "CPU Temp (°C)"
    ]

    columns_to_show = [col for col in columns_to_show if col in top_spikes_display.columns]

    return top_spikes_display[columns_to_show]


def create_pdf_report(df, fig, spikes, top_spikes_display, fps_threshold):
    pdf_buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Game Performance Analyzer - PDF Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Performance Summary", styles["Heading2"]))

    summary_rows = [["Metric", "Value"]]

    if "FPS" in df.columns:
        summary_rows += [
            ["Average FPS", f"{df['FPS'].mean():.2f}"],
            ["Minimum FPS", f"{df['FPS'].min():.2f}"],
            ["Maximum FPS", f"{df['FPS'].max():.2f}"],
        ]

    if "Frametime" in df.columns:
        summary_rows += [
            ["Average Frame Time", f"{df['Frametime'].mean():.2f} ms"],
            ["Maximum Frame Time", f"{df['Frametime'].max():.2f} ms"],
        ]

    if "CPU" in df.columns:
        summary_rows.append(["Average CPU Usage", f"{df['CPU'].mean():.2f}%"])

    if "GPU" in df.columns:
        summary_rows.append(["Average GPU Usage", f"{df['GPU'].mean():.2f}%"])

    if "Temp" in df.columns:
        summary_rows.append(["Average GPU Temperature", f"{df['Temp'].mean():.2f} °C"])

    if "CPU Temp" in df.columns:
        summary_rows.append(["Average CPU Temperature", f"{df['CPU Temp'].mean():.2f} °C"])

    summary_rows.append(["FPS Threshold Used", f"{fps_threshold} FPS"])
    summary_rows.append(["Number of FPS Spikes Detected", str(len(spikes))])

    summary_table = Table(summary_rows, colWidths=[3.2 * inch, 2.2 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F3F4F6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 18))

    elements.append(Paragraph("Most Severe FPS Spikes", styles["Heading2"]))

    if top_spikes_display.empty:
        elements.append(Paragraph("No FPS spikes were detected for the selected threshold.", styles["Normal"]))
    else:
        elements.append(Paragraph(
            "The table below shows up to 10 of the most severe FPS drops, sorted by lowest FPS.",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 8))

        spike_rows = [list(top_spikes_display.columns)]

        for _, row in top_spikes_display.iterrows():
            spike_rows.append([
                f"{value:.2f}" if isinstance(value, float) else str(value)
                for value in row
            ])

        spike_table = Table(spike_rows, repeatRows=1)
        spike_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FAFAFA")),
        ]))
        elements.append(spike_table)

    elements.append(Spacer(1, 18))
    elements.append(Paragraph("Performance Graphs", styles["Heading2"]))

    chart_buffer = io.BytesIO()
    fig.savefig(chart_buffer, format="png", dpi=160, bbox_inches="tight")
    chart_buffer.seek(0)

    elements.append(Image(chart_buffer, width=7.2 * inch, height=5.4 * inch))

    doc.build(elements)

    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()

    return pdf_bytes


file = st.file_uploader("Upload log (.hml or .csv)", type=["hml", "csv", "txt"])

if file:
    df = parse_afterburner_log(file)

    if df.empty:
        st.error("No valid performance data was found in the uploaded file.")
        st.stop()

    with st.expander("Data preview"):
        st.dataframe(df.head(20), use_container_width=True)

    st.subheader("Performance Summary")

    columns = st.columns(6)

    if "FPS" in df.columns:
        columns[0].metric("🎮 Average FPS", f"{df['FPS'].mean():.2f}")
    else:
        columns[0].metric("🎮 Average FPS", "N/A")

    if "Frametime" in df.columns:
        columns[1].metric("⏱️ Average Frame Time", f"{df['Frametime'].mean():.2f} ms")
    else:
        columns[1].metric("⏱️ Average Frame Time", "N/A")

    if "CPU" in df.columns:
        columns[2].metric("🧠 Average CPU Usage", f"{df['CPU'].mean():.2f}%")
    else:
        columns[2].metric("🧠 Average CPU Usage", "N/A")

    if "GPU" in df.columns:
        columns[3].metric("🎨 Average GPU Usage", f"{df['GPU'].mean():.2f}%")
    else:
        columns[3].metric("🎨 Average GPU Usage", "N/A")

    if "Temp" in df.columns:
        columns[4].metric("🌡️ Average GPU Temp", f"{df['Temp'].mean():.2f} °C")
    else:
        columns[4].metric("🌡️ Average GPU Temp", "N/A")

    if "CPU Temp" in df.columns:
        columns[5].metric("🔥 Average CPU Temp", f"{df['CPU Temp'].mean():.2f} °C")
    else:
        columns[5].metric("🔥 Average CPU Temp", "N/A")

    st.subheader("Detected Performance Spikes")

    fps_threshold = st.slider("FPS threshold for spike detection", 10, 120, 50)

    if "FPS" in df.columns:
        spikes = df[df["FPS"] < fps_threshold]
    else:
        spikes = pd.DataFrame()

    top_spikes_display = build_top_spikes_table(spikes)

    if len(spikes) > 0:
        st.warning(
            f"{len(spikes)} FPS spikes were detected below the selected threshold of {fps_threshold} FPS."
        )
        st.caption("The table shows up to 10 of the most severe spikes, sorted by lowest FPS.")
        st.dataframe(top_spikes_display, use_container_width=True)
    else:
        st.success("No FPS spikes were detected for the selected threshold.")

    st.subheader("Performance Graphs")

    fig = build_performance_chart(df)
    st.pyplot(fig)

    pdf_bytes = create_pdf_report(
        df=df,
        fig=fig,
        spikes=spikes,
        top_spikes_display=top_spikes_display,
        fps_threshold=fps_threshold
    )

    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name="game_performance_report.pdf",
        mime="application/pdf"
    )
