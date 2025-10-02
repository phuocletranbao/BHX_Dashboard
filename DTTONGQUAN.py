import streamlit as st
import pandas as pd

# ===== 1. Đọc file =====
file_now  = "data.xlsx"   # tháng hiện tại
file_old  = "data3.xlsx"  # tổng 3 tháng trước
file_nh   = "nh.xlsx"     # mapping ngành hàng -> nhóm

df_now = pd.read_excel(file_now)
df_old = pd.read_excel(file_old)
mapping = pd.read_excel(file_nh)

# ===== 2. Chuẩn hóa =====
df_now.columns = df_now.columns.str.strip()
df_old.columns = df_old.columns.str.strip()
mapping.columns = mapping.columns.str.strip()

# Merge nhóm ngành
df_now = df_now.merge(mapping, on="Ngành hàng", how="left")
df_old = df_old.merge(mapping, on="Ngành hàng", how="left")

# ===== 3. Chọn siêu thị =====
list_sieuthi = df_now["Mã siêu thị"].unique()
chon_sieuthi = st.selectbox("Chọn siêu thị", list_sieuthi)

df_now = df_now[df_now["Mã siêu thị"] == chon_sieuthi]
df_old = df_old[df_old["Mã siêu thị"] == chon_sieuthi]

# ===== 4. Hàm tính toán tổng quan =====
def tinh_tong_quan(data):
    tong_sl = data["Tổng số lượng"].sum()
    tong_dt = data["Tổng doanh thu"].sum()
    nhom = data.groupby("Nhóm")["Tổng doanh thu"].sum().to_dict()
    return tong_sl, tong_dt, nhom.get("FRESH",0), nhom.get("FMCG",0), nhom.get("ĐÔNG MÁT",0)

now_sl, now_dt, now_fresh, now_fmcg, now_dm = tinh_tong_quan(df_now)
old_sl, old_dt, old_fresh, old_fmcg, old_dm = tinh_tong_quan(df_old)

# Trung bình 3 tháng
old_sl /= 3; old_dt /= 3; old_fresh /= 3; old_fmcg /= 3; old_dm /= 3

def calc_change(new, old):
    if old == 0:
        return 0 if new == 0 else 100
    return (new-old)/old*100

# ===== 5. Style cho % thay đổi =====
def style_change(val):
    if val < 0:
        return f"<span style='color:red'>{val:.2f}%</span>"
    elif val > 5:
        return f"<span style='color:green'>{val:.2f}%</span>"
    else:
        return f"{val:.2f}%"

# ===== 6. Hiển thị chỉ số tổng quan =====
st.title("📊 Báo cáo Doanh thu theo Siêu thị")
st.subheader(f"🏬 Siêu thị: {chon_sieuthi}")

st.markdown("### 🔹 Chỉ số tổng quan")

tong_quan = {
    "Tổng SL": (now_sl, calc_change(now_sl, old_sl)),
    "Tổng DT": (now_dt, calc_change(now_dt, old_dt)),
    "Doanh thu FRESH": (now_fresh, calc_change(now_fresh, old_fresh)),
    "Doanh thu FMCG": (now_fmcg, calc_change(now_fmcg, old_fmcg)),
    "Doanh thu ĐÔNG MÁT": (now_dm, calc_change(now_dm, old_dm)),
}

for k,(v,c) in tong_quan.items():
    st.markdown(f"**{k}:** {int(v):,} (% TB 3 Tháng: {style_change(c)})", unsafe_allow_html=True)

# ===== 7. Doanh thu theo Ngành hàng =====
st.markdown("### 🔹 Doanh thu theo Ngành hàng (theo Nhóm)")

# Gom dữ liệu hiện tại
nh_now = df_now.groupby(["Nhóm","Ngành hàng"], as_index=False).agg({
    "Tổng số lượng":"sum",
    "Tổng doanh thu":"sum"
})

# Gom dữ liệu 3 tháng trước
nh_old = df_old.groupby(["Nhóm","Ngành hàng"], as_index=False).agg({
    "Tổng số lượng":"sum",
    "Tổng doanh thu":"sum"
})
nh_old["Tổng số lượng"] /= 3
nh_old["Tổng doanh thu"] /= 3

# Merge 2 bảng
nh_merge = nh_now.merge(
    nh_old,
    on=["Nhóm","Ngành hàng"],
    how="left",
    suffixes=("","_old")
).fillna(0)

# Chỉ giữ lại 3 nhóm cần thiết
nh_merge = nh_merge[nh_merge["Nhóm"].isin(["FRESH","FMCG","ĐÔNG MÁT"])]

# Tính % thay đổi so với TB 3 tháng
nh_merge["% TB 3 Tháng"] = nh_merge.apply(
    lambda r: calc_change(r["Tổng doanh thu"], r["Tổng doanh thu_old"]),
    axis=1
)

# Format hiển thị
nh_merge["Tổng số lượng"] = nh_merge["Tổng số lượng"].astype(int).map("{:,}".format)
nh_merge["Tổng doanh thu"] = nh_merge["Tổng doanh thu"].astype(int).map("{:,}".format)
nh_merge["% TB 3 Tháng"] = nh_merge["% TB 3 Tháng"].apply(lambda x: style_change(x))

# Sắp xếp để hiển thị đẹp hơn
nh_merge = nh_merge.sort_values(["Nhóm","Tổng doanh thu"], ascending=[True, False])

# Hiển thị bảng
st.write(
    nh_merge[["Nhóm","Ngành hàng","Tổng số lượng","Tổng doanh thu","% TB 3 Tháng"]]
    .to_html(escape=False,index=False),
    unsafe_allow_html=True
)

# ===== 8. Top 5 model theo 5 ngành hàng doanh thu cao nhất =====
st.markdown("### 🔹 Top 5 Model theo 5 ngành hàng doanh thu cao nhất")

# Lấy 5 ngành hàng doanh thu cao nhất
nganh_top = (
    df_now.groupby("Ngành hàng")["Tổng doanh thu"]
          .sum()
          .sort_values(ascending=False)
          .head(5)
          .index
)

for nganh in nganh_top:
    df_n = df_now[df_now["Ngành hàng"]==nganh]
    df_o = df_old[df_old["Ngành hàng"]==nganh]

    if df_n.empty: 
        continue

    # Top 5 model hiện tại
    top_now = df_n.groupby("Model",as_index=False).agg({"Tổng số lượng":"sum","Tổng doanh thu":"sum"})
    top_now = top_now.sort_values("Tổng doanh thu",ascending=False).head(5)

    # Doanh thu trung bình 3 tháng trước
    top_old = df_o.groupby("Model",as_index=False).agg({"Tổng doanh thu":"sum"})
    top_old["Tổng doanh thu"] = top_old["Tổng doanh thu"]/3

    # Merge để tính % thay đổi
    top_merge = top_now.merge(top_old,on="Model",how="left",suffixes=("","_old")).fillna(0)
    top_merge["% TB 3 Tháng"] = top_merge.apply(lambda r: calc_change(r["Tổng doanh thu"], r["Tổng doanh thu_old"]), axis=1)

    # Format hiển thị
    top_merge["Tổng số lượng"] = top_merge["Tổng số lượng"].astype(int).map("{:,}".format)
    top_merge["Tổng doanh thu"] = top_merge["Tổng doanh thu"].astype(int).map("{:,}".format)
    top_merge["% TB 3 Tháng"] = top_merge["% TB 3 Tháng"].apply(lambda x: style_change(x))

    tong_nganh = df_n["Tổng doanh thu"].sum()
    st.markdown(f"#### 🛒 {nganh} (Tổng doanh thu: {tong_nganh:,.0f})")
    st.write(top_merge[["Model","Tổng số lượng","Tổng doanh thu","% TB 3 Tháng"]].to_html(escape=False,index=False), unsafe_allow_html=True)
