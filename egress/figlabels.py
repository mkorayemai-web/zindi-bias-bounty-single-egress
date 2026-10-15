"""Figure helpers (the author cannot view images, so layout is verified numerically):
 place_labels : greedy label placement with leader lines; a label is accepted only if its box lies inside the axes and overlaps no earlier label / avoid-box
 qa           : text-vs-text overlap and out-of-figure check over EVERY Text artist of a figure (tick labels, titles, legends, colour bar, annotations)
 north_arrow  : arrow pointing to TRUE north on a map drawn in a projected CRS (rotated by the grid convergence, computed numerically)"""
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.text import Text

CANDS = [(8, 6, "left", "bottom"), (8, -6, "left", "top"), (-8, 6, "right", "bottom"), (-8, -6, "right", "top"), (0, 12, "center", "bottom"), (0, -12, "center", "top"),
         (22, 16, "left", "bottom"), (22, -16, "left", "top"), (-22, 16, "right", "bottom"), (-22, -16, "right", "top"), (34, 0, "left", "center"), (-34, 0, "right", "center"),
         (40, 30, "left", "bottom"), (40, -30, "left", "top"), (-40, 30, "right", "bottom"), (-40, -30, "right", "top"), (0, 36, "center", "bottom"), (0, -36, "center", "top"),
         (60, 44, "left", "bottom"), (60, -44, "left", "top"), (-60, 44, "right", "bottom"), (-60, -44, "right", "top")]

def _overlap(a, b, m=1.0):
    return not (a[2] <= b[0] + m or a[0] >= b[2] - m or a[3] <= b[1] + m or a[1] >= b[3] - m)

def place_labels(fig, ax, xs, ys, texts, fontsize=6.5, color="#0b3d91", avoid=(), bbox_alpha=0.8):
    r = fig.canvas.get_renderer(); k = fig.dpi / 72.0; ab = ax.get_window_extent(r); axb = (ab.x0 + 2, ab.y0 + 2, ab.x1 - 2, ab.y1 - 2)
    fp = FontProperties(size=fontsize); padp = 0.12 * fontsize * k
    placed = [tuple(a) for a in avoid]; done, skipped = [], []
    for x, y, s in zip(xs, ys, texts):
        px, py = ax.transData.transform((x, y)); w, h, _ = r.get_text_width_height_descent(s, fp, False); w += 2 * padp; h += 2 * padp
        chosen = None
        for dx, dy, ha, va in CANDS:
            ax0, ay0 = px + dx * k, py + dy * k
            x0 = ax0 - (w if ha == "right" else (w / 2 if ha == "center" else 0)); y0 = ay0 - (h if va == "top" else (h / 2 if va == "center" else 0))
            bb = (x0, y0, x0 + w, y0 + h)
            if bb[0] < axb[0] or bb[1] < axb[1] or bb[2] > axb[2] or bb[3] > axb[3]: continue
            if any(_overlap(bb, p) for p in placed): continue
            chosen = (dx, dy, ha, va, bb); break
        if chosen is None: skipped.append(s); continue
        dx, dy, ha, va, bb = chosen; placed.append(bb)
        far = np.hypot(dx, dy) > 14
        ax.annotate(s, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, fontsize=fontsize, color=color, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=bbox_alpha),
                    arrowprops=dict(arrowstyle="-", lw=0.5, color=color, shrinkA=0, shrinkB=1.5) if far else None)
        done.append(s)
    return done, skipped

def qa(fig, tag):
    fig.canvas.draw(); r = fig.canvas.get_renderer(); W, H = fig.canvas.get_width_height(); items = []
    hidden = set()                                   # tick labels / axis labels of axes switched off with set_axis_off() are never drawn
    for a_ in fig.axes:
        for axis in (a_.xaxis, a_.yaxis):                # tick labels whose tick lies outside the view interval are never drawn
            lo, hi = sorted(axis.get_view_interval())
            for tk in axis.get_major_ticks() + axis.get_minor_ticks():
                if not (lo - 1e-9 <= tk.get_loc() <= hi + 1e-9): hidden.add(id(tk.label1)); hidden.add(id(tk.label2))
        if not a_.axison:
            for axis in (a_.xaxis, a_.yaxis): hidden.update(id(t) for t in axis.get_ticklabels(which="both")); hidden.add(id(axis.label)); hidden.add(id(axis.offsetText))
    for t in fig.findobj(Text):
        s = t.get_text().strip()
        if not s or not t.get_visible() or id(t) in hidden: continue
        bb = Text.get_window_extent(t, r)
        if bb.width < 1 or bb.height < 1: continue
        items.append((s, bb))
    out = [s[:30] for s, bb in items if bb.x0 < -0.5 or bb.y0 < -0.5 or bb.x1 > W + 0.5 or bb.y1 > H + 0.5]
    ov = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]; ix = min(a.x1, b.x1) - max(a.x0, b.x0); iy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ix > 1.0 and iy > 1.0: ov.append((items[i][0][:28], items[j][0][:28], round(ix), round(iy)))
    print(f"QA {tag}: {len(items)} texts | out of figure: {out} | overlapping pairs: {ov}")
    return out, ov

def north_arrow(ax, theta_deg, xy=(0.90, 0.10), L=0.075):
    """theta_deg = clockwise angle of TRUE north from 'up' on the map (0 when the map is plate carree / north-up)."""
    th = np.radians(theta_deg); x0, y0 = xy
    ax.annotate("", xy=(x0 + L * np.sin(th), y0 + L * np.cos(th)), xytext=(x0, y0), xycoords="axes fraction", textcoords="axes fraction", arrowprops=dict(arrowstyle="-|>", lw=1.2, color="k"), zorder=9)
    ax.text(x0 + (L + 0.04) * np.sin(th), y0 + (L + 0.04) * np.cos(th), "N", transform=ax.transAxes, ha="center", va="center", fontsize=8, fontweight="bold", zorder=9, bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))
