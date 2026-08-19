import matplotlib.pyplot as plt
from pathlib import Path

equations = {
    "eq_ldr": r"R_{\mathrm{LDR}} = R_0 \cdot \left(\frac{E_0}{E}\right)^\gamma",
    "eq_vout": r"V_{\mathrm{out}} = V_{\mathrm{CC}} \cdot \left( \frac{R_R}{R_{\mathrm{LDR}} + R_R} \right)",
    "eq_lux": r"\mathrm{Lux} = \mathrm{map}(\mathrm{ADC}, 0, 1023, 0, 1000)",
    "eq_si": r"S_i(x_i) = 100 \cdot \exp\left( -\frac{(x_i - x_{\mathrm{ideal},i})^2}{2\sigma_i^2} \right)",
    "eq_comfort": r"C = \sum_{i \in \{T, H, L\}} w_i \cdot S_i(x_i)",
    "eq_mean": r"\bar{x} = \frac{1}{N} \sum_{k=1}^{N} x_k",
    "eq_minmax": r"x_{\mathrm{min}} = \min_{1 \leq k \leq N} (x_k), \ \ \ x_{\mathrm{max}} = \max_{1 \leq k \leq N} (x_k)",
    "eq_range": r"R = x_{\mathrm{max}} - x_{\mathrm{min}}"
}

output_dir = Path("/home/dicson/Arduino/trabajo/math_images")
output_dir.mkdir(exist_ok=True)

for name, latex_str in equations.items():
    fig = plt.figure(figsize=(6, 0.8), dpi=300)
    fig.patch.set_facecolor('#F8FAFC') # Light slate background box
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.text(0.5, 0.5, f"${latex_str}$", fontsize=15, ha='center', va='center', color='#1E3A8A')
    plt.savefig(output_dir / f"{name}.png", bbox_inches='tight', pad_inches=0.1, dpi=300, facecolor='#F8FAFC')
    plt.close(fig)

print("Imágenes de ecuaciones generadas correctamente.")
