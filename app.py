import os
import glob
from pathlib import Path
import streamlit as st
import ollama
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

INBOX_DIR = Path("inbox")
PROCESSED_DIR = Path("processed")

INBOX_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="💪 Physio & Sports Command Center", layout="wide")
st.title("💪 PHYSIO & SPORTS COMMAND CENTER")
st.caption("Universal Adaptive Biomechanical & Sports Analytics • Local AI Intelligence")

# -------------------------------------------------------------
# Heuristic & Universal Dataset Profiler (Works for ANY dataset)
# -------------------------------------------------------------
def analyze_any_dataset(df, file_name=""):
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    
    # 1. Detect Subject / Athlete Identifier column
    id_keywords = ['id', 'zawodnik', 'name', 'imię', 'nazwisko', 'athlete', 'player', 'subject', 'patient', 'uczestnik', 'osoba']
    subject_candidates = [c for c in df.columns if any(k in c.lower() for k in id_keywords)]
    subject_col = subject_candidates[0] if subject_candidates else (cat_cols[0] if cat_cols else None)
    
    # 2. Detect Grouping / Segmentation columns (categorical or low-cardinality discrete numeric)
    group_candidates = [c for c in cat_cols if 1 < df[c].nunique() <= 35 and c != subject_col]
    if not group_candidates:
        group_candidates = [c for c in num_cols if 1 < df[c].nunique() <= 12]
        
    # 3. Check for specific known frameworks (Eurofit, Biodex)
    cols_lower = [c.lower() for c in df.columns]
    eurofit_keywords = ['flamingo', 'plate tapping', 'sit and reach', 'handgrip', 'beep test', 'bieg 10x5m', 'skok w dal', 'zwis']
    biodex_keywords = ['peak torque', 'ruch', 'strona', 'deficit (%)', 'total work', 'agon/antag']
    
    is_eurofit = any(any(kw in c for kw in eurofit_keywords) for c in cols_lower)
    is_biodex = any(any(kw in c for kw in biodex_keywords) for c in cols_lower)
    
    if is_eurofit:
        dtype = "Eurofit Physical Fitness Battery"
        default_prompt = (
            "You are an expert sports scientist, physiologist, and athletic performance analyst. "
            "I will provide you with statistical results from the Eurofit Physical Fitness Battery. "
            "Analyze the performance differences across disciplines and genders, identify physiological strengths and weaknesses "
            "(aerobic capacity, explosive power, muscular endurance, agility, flexibility, balance), assess physical readiness, "
            "and provide actionable coaching, athletic conditioning, and injury prevention recommendations."
        )
    elif is_biodex:
        dtype = "Biodex Isokinetic Dynamometry"
        default_prompt = (
            "You are an expert sports physiotherapist and biomechanist. "
            "I will provide you with a descriptive statistical summary of a patient's isokinetic dynamometry (Biodex). "
            "Analyze the differences between the Right and Left sides across different speeds and movements. "
            "Identify any significant deficits, bilateral imbalances, agonist/antagonist ratios, or potential injury risks. "
            "Provide a professional, concise, and structured clinical rehabilitation report with targeted corrective exercises."
        )
    else:
        dtype = "Custom Sports / Biomechanical Dataset"
        top_metrics = ", ".join(num_cols[:6])
        top_groups = ", ".join(group_candidates[:3]) if group_candidates else "the overall sample"
        default_prompt = (
            f"You are an expert sports scientist, clinical biomechanist, and performance analyst. "
            f"I will provide you with statistical results from the dataset '{file_name}'. "
            f"Primary quantitative metrics include: {top_metrics}. "
            f"Key grouping categories include: {top_groups}. "
            f"Analyze the performance patterns and distributions across the groups, identify notable outliers or deficits, "
            f"evaluate functional capacities and potential risks, and provide actionable conclusions and evidence-based recommendations."
        )
        
    return {
        "type": dtype,
        "is_eurofit": is_eurofit,
        "is_biodex": is_biodex,
        "is_custom": not (is_eurofit or is_biodex),
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "subject_col": subject_col,
        "group_candidates": group_candidates,
        "default_prompt": default_prompt
    }

# -------------------------------------------------------------
# Helper: Fetch Ollama Models safely
# -------------------------------------------------------------
@st.cache_data(ttl=60)
def get_available_models():
    try:
        response = ollama.list()
        models_list = getattr(response, 'models', response.get('models', []))
        names = []
        for m in models_list:
            if hasattr(m, 'model'):
                names.append(m.model)
            elif isinstance(m, dict) and 'name' in m:
                names.append(m['name'])
            elif isinstance(m, dict) and 'model' in m:
                names.append(m['model'])
        if names:
            # Prioritize 4b and lightweight models so heavy 24GB models aren't picked by default
            def model_priority(name):
                n = name.lower()
                if 'nano:4b' in n or ':4b' in n:
                    return 0
                if '3b' in n or '2b' in n or '1.5b' in n or '1.7b' in n:
                    return 1
                if '8b' in n or '7b' in n:
                    return 2
                return 3
            return sorted(names, key=model_priority)
    except Exception:
        pass
    return ["nemotron-3-nano:4b", "nemotron-3-nano:latest", "llama3.2:3b", "qwen2.5:3b"]

available_models = get_available_models()

# -------------------------------------------------------------
# Sidebar: Settings & Data Source
# -------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ AI Configuration")
    model_name = st.selectbox("Ollama Model", available_models, index=0)
    
    ctx_size = st.slider("Context size", 2048, 32768, 8192, step=1024)
    max_tokens = st.slider("Max output tokens", 1024, 8192, 4096, step=512)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.4, step=0.1)
    
    if st.button("🧹 Clear session"):
        st.session_state.clear()
        st.rerun()
        
    st.divider()
    st.header("📂 Data Source")
    
    inbox_files = glob.glob(str(INBOX_DIR / "*.xlsx")) + glob.glob(str(INBOX_DIR / "*.csv"))
    if not inbox_files:
        st.warning("No Excel/CSV files found in inbox/")
        selected_file = None
    else:
        file_names = [Path(f).name for f in inbox_files]
        selected_file_name = st.selectbox("Select file to analyze", file_names)
        selected_file = INBOX_DIR / selected_file_name

@st.cache_data
def load_data(file_path):
    if not file_path:
        return None
    try:
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

df = load_data(selected_file)

if df is not None:
    profile = analyze_any_dataset(df, selected_file.name)
    
    # Header Banner
    col_b1, col_b2 = st.columns([3, 1])
    with col_b1:
        st.info(f"🎯 **Identified Schema:** `{profile['type']}` | **File:** `{selected_file.name}` ({len(df)} rows, {len(df.columns)} columns)")
    with col_b2:
        if st.button("✨ Tailor with AI", help="Prompt local LLM to deeply inspect column semantics and tailor recommendations"):
            with st.spinner("AI is analyzing column semantics and dataset domain..."):
                try:
                    summary_cols = ", ".join(df.columns.tolist()[:20])
                    preview = df.head(3).to_string()
                    prompt = (
                        f"You are an expert sports scientist and biomechanical statistician.\n"
                        f"Analyze this dataset:\n"
                        f"Filename: {selected_file.name}\n"
                        f"Columns: {summary_cols}\n"
                        f"Sample rows:\n{preview}\n\n"
                        f"Please provide:\n"
                        f"1. What kind of test/battery/measurement this is (Domain & Context).\n"
                        f"2. Top 3 key performance indicators (KPIs) to focus on.\n"
                        f"3. Recommended grouping columns for comparative analysis.\n"
                        f"4. Key clinical or athletic questions this data answers."
                    )
                    ai_resp = ollama.chat(
                        model=model_name,
                        messages=[{'role': 'user', 'content': prompt}],
                        options={"num_ctx": 4096, "num_predict": 768}
                    )
                    st.session_state['ai_tailor_summary'] = ai_resp['message']['content']
                except Exception as ex:
                    st.session_state['ai_tailor_summary'] = f"AI profiling note: {ex}"
    
    if 'ai_tailor_summary' in st.session_state:
        with st.expander("🤖 AI Dataset Intelligence Brief", expanded=True):
            st.markdown(st.session_state['ai_tailor_summary'])
            
    # Main Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Data & Stats", "📈 Visualizations", "🤖 AI Assessment"])
    
    # -------------------------------------------------------------
    # TAB 1: DATA & DESCRIPTIVE STATS (UNIVERSAL)
    # -------------------------------------------------------------
    with tab1:
        st.subheader("Dataset Overview")
        st.dataframe(df.head(10), use_container_width=True)
        
        st.divider()
        st.subheader("Dynamic Grouped Statistics")
        
        avail_cats = profile['cat_cols']
        avail_nums = profile['num_cols']
        
        c_grp, c_metric = st.columns([1, 2])
        with c_grp:
            selected_group = st.multiselect(
                "Group by columns:",
                options=avail_cats + [c for c in avail_nums if df[c].nunique() < 15],
                default=[g for g in profile['group_candidates'] if g in df.columns][:2]
            )
        with c_metric:
            selected_metrics = st.multiselect(
                "Metrics to aggregate:",
                options=avail_nums,
                default=avail_nums[:8]
            )
            
        if selected_group and selected_metrics:
            try:
                grouped_stats = df.groupby(selected_group)[selected_metrics].agg(['mean', 'std', 'min', 'max']).round(2)
                st.dataframe(grouped_stats, use_container_width=True)
                st.session_state['stats_text'] = grouped_stats.to_string()
            except Exception as e:
                st.error(f"Grouping calculation note: {e}")
                st.dataframe(df.describe())
                st.session_state['stats_text'] = df.describe().to_string()
        else:
            st.dataframe(df.describe().round(2), use_container_width=True)
            st.session_state['stats_text'] = df.describe().round(2).to_string()

    # -------------------------------------------------------------
    # TAB 2: VISUALIZATIONS (PRESETS + UNIVERSAL SUITE)
    # -------------------------------------------------------------
    with tab2:
        # Check if Eurofit
        if profile['is_eurofit']:
            st.subheader("🏃 Eurofit Physical Fitness Battery Analytics")
            vtab1, vtab2, vtab3, vtab4, vtab_custom = st.tabs([
                "🏆 Discipline & Gender Benchmarks", 
                "🕸️ Athlete Spider Profile", 
                "📉 Anthropometrics & Correlates",
                "🔥 Correlation Heatmap",
                "🛠️ Custom Chart Studio"
            ])
            
            eurofit_test_cols = [
                c for c in [
                    'Flamingo [próby/60s]', 'Plate Tapping [s]', 'Sit and Reach [cm]',
                    'Skok w dal z m. [cm]', 'Handgrip [kg]', 'Brzuszki 30s [powt.]',
                    'Zwis na ramionach [s]', 'Bieg 10x5m [s]', 'Beep Test [poziom]'
                ] if c in df.columns
            ] or profile['num_cols']
                
            with vtab1:
                col_ef1, col_ef2 = st.columns([1, 1])
                with col_ef1:
                    test_to_plot = st.selectbox("Select Fitness Test:", eurofit_test_cols, index=min(len(eurofit_test_cols)-1, 8))
                with col_ef2:
                    group_by_col = st.selectbox("Group / Color by:", [c for c in ['Dyscyplina', 'Płeć'] if c in df.columns] or profile['group_candidates'], index=0)
                    
                fig_ef = px.box(
                    df, 
                    x=group_by_col, 
                    y=test_to_plot, 
                    color='Płeć' if 'Płeć' in df.columns and group_by_col != 'Płeć' else group_by_col,
                    points="all",
                    title=f"Distribution of {test_to_plot} across {group_by_col}",
                    template="plotly_white"
                )
                st.plotly_chart(fig_ef, use_container_width=True)
                
            with vtab2:
                st.markdown("#### Multi-Test Percentile Radar Chart")
                id_col = 'ID Sportowca' if 'ID Sportowca' in df.columns else (profile['subject_col'] or df.columns[0])
                name_col = 'Nazwisko' if 'Nazwisko' in df.columns else id_col
                
                athlete_labels = [f"{df.loc[i, id_col]} - {df.loc[i, name_col]}" if name_col in df.columns and name_col != id_col else str(df.loc[i, id_col]) for i in df.index]
                selected_ath_idx = st.selectbox("Select Athlete to Profile:", range(len(df)), format_func=lambda x: athlete_labels[x])
                
                athlete_row = df.iloc[selected_ath_idx]
                inverted_tests = {'Flamingo [próby/60s]', 'Plate Tapping [s]', 'Bieg 10x5m [s]'}
                pct_df = pd.DataFrame(index=df.index)
                for t in eurofit_test_cols:
                    if t in inverted_tests:
                        pct_df[t] = df[t].rank(pct=True, ascending=False) * 100
                    else:
                        pct_df[t] = df[t].rank(pct=True, ascending=True) * 100
                
                ath_pcts = [pct_df.loc[selected_ath_idx, t] for t in eurofit_test_cols]
                labels_clean = [t.split(' [')[0] for t in eurofit_test_cols]
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=ath_pcts + [ath_pcts[0]],
                    theta=labels_clean + [labels_clean[0]],
                    fill='toself',
                    name=f"Athlete: {athlete_labels[selected_ath_idx]}",
                    line=dict(color='#00CC96', width=2)
                ))
                
                if 'Dyscyplina' in df.columns:
                    disc = athlete_row['Dyscyplina']
                    disc_pcts = [pct_df.loc[df['Dyscyplina'] == disc, t].mean() for t in eurofit_test_cols]
                    fig_radar.add_trace(go.Scatterpolar(
                        r=disc_pcts + [disc_pcts[0]],
                        theta=labels_clean + [labels_clean[0]],
                        name=f"Discipline Avg ({disc})",
                        line=dict(color='#636EFA', dash='dash')
                    ))
                    
                fig_radar.add_trace(go.Scatterpolar(
                    r=[50] * (len(labels_clean) + 1),
                    theta=labels_clean + [labels_clean[0]],
                    name="Cohort Median (50th percentile)",
                    line=dict(color='#FFA15A', dash='dot')
                ))
                
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=True,
                    title="Eurofit Physical Performance Percentile Radar (Higher = Better)"
                )
                st.plotly_chart(fig_radar, use_container_width=True)
                
            with vtab3:
                col_sc1, col_sc2 = st.columns(2)
                with col_sc1:
                    x_sc = st.selectbox("Anthropometric / Predictor (X):", [c for c in ['Wzrost [cm]', 'Waga [kg]', 'BMI [kg/m²]', 'Wiek [lata]'] if c in df.columns] or profile['num_cols'], index=0)
                with col_sc2:
                    y_sc = st.selectbox("Physical Test Output (Y):", eurofit_test_cols, index=min(len(eurofit_test_cols)-1, 3))
                    
                fig_scatter = px.scatter(
                    df, x=x_sc, y=y_sc, 
                    color='Dyscyplina' if 'Dyscyplina' in df.columns else None,
                    symbol='Płeć' if 'Płeć' in df.columns else None,
                    trendline="ols",
                    title=f"Correlation: {x_sc} vs {y_sc}",
                    template="plotly_white"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
                
            with vtab4:
                corr_matrix = df[eurofit_test_cols].corr().round(2)
                fig_heat = px.imshow(corr_matrix, text_auto=True, color_continuous_scale="RdBu_r", aspect="auto", title="Eurofit Correlation Heatmap")
                st.plotly_chart(fig_heat, use_container_width=True)
                
            with vtab_custom:
                st.markdown("#### 🛠️ Custom Chart Studio")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    c_type = st.selectbox("Chart Type", ["Scatter", "Box", "Bar", "Histogram"], key="ef_chart_type")
                with c2:
                    x_col = st.selectbox("X Axis", df.columns, index=0, key="ef_x")
                with c3:
                    y_col = st.selectbox("Y Axis", profile['num_cols'], index=0, key="ef_y")
                with c4:
                    color_col = st.selectbox("Color / Group", ["None"] + profile['cat_cols'], key="ef_color")
                col_p = None if color_col == "None" else color_col
                if c_type == "Scatter":
                    st.plotly_chart(px.scatter(df, x=x_col, y=y_col, color=col_p, template="plotly_white"), use_container_width=True)
                elif c_type == "Box":
                    st.plotly_chart(px.box(df, x=x_col, y=y_col, color=col_p, template="plotly_white"), use_container_width=True)
                elif c_type == "Bar":
                    st.plotly_chart(px.bar(df, x=x_col, y=y_col, color=col_p, template="plotly_white"), use_container_width=True)
                else:
                    st.plotly_chart(px.histogram(df, x=y_col, color=col_p, template="plotly_white"), use_container_width=True)
                    
        # Check if Biodex
        elif profile['is_biodex']:
            st.subheader("🦵 Biodex Isokinetic Dynamometry Analytics")
            col1, col2 = st.columns(2)
            with col1:
                if 'Prędkość (°/s)' in df.columns and 'Peak Torque (N-m)' in df.columns:
                    st.plotly_chart(px.box(df, x="Prędkość (°/s)", y="Peak Torque (N-m)", color="Strona" if "Strona" in df.columns else None, facet_col="Ruch" if "Ruch" in df.columns else None, title="Peak Torque Asymmetry by Speed & Movement"), use_container_width=True)
            with col2:
                if 'Prędkość (°/s)' in df.columns and 'Total Work (J)' in df.columns:
                    st.plotly_chart(px.box(df, x="Prędkość (°/s)", y="Total Work (J)", color="Strona" if "Strona" in df.columns else None, facet_col="Ruch" if "Ruch" in df.columns else None, title="Total Work Asymmetry by Speed"), use_container_width=True)
            st.divider()
            if 'Zawodnik' in df.columns and 'Avg. Power (W)' in df.columns:
                grp_power = df.groupby(['Zawodnik', 'Ruch', 'Strona', 'Prędkość (°/s)'])['Avg. Power (W)'].mean().reset_index()
                st.plotly_chart(px.bar(grp_power, x="Prędkość (°/s)", y="Avg. Power (W)", color="Strona", facet_row="Zawodnik", facet_col="Ruch", barmode="group", title="Average Power Comparison"), use_container_width=True)
                
        # UNIVERSAL ANALYTICS SUITE FOR ANY CUSTOM DATASET
        else:
            st.subheader("🌐 Universal Biomechanical & Sports Analytics Suite")
            utab1, utab2, utab3, utab4, utab5, utab6 = st.tabs([
                "📊 Group Breakdown & Distributions",
                "🏆 Subject Ranking / Leaderboard",
                "🕸️ Multi-Metric Subject Radar",
                "📉 Bivariate Trends & Regressions",
                "🔥 Correlation Matrix Heatmap",
                "🛠️ Custom Chart Studio"
            ])
            
            with utab1:
                col_u1, col_u2, col_u3 = st.columns([1, 1, 1])
                with col_u1:
                    metric_u = st.selectbox("Metric to evaluate (Y):", profile['num_cols'], index=0, key="u_metric")
                with col_u2:
                    group_u = st.selectbox("Group by (X):", profile['group_candidates'] or profile['cat_cols'] or [df.columns[0]], index=0, key="u_group")
                with col_u3:
                    subgroup_opts = ["None"] + [c for c in (profile['group_candidates'] or profile['cat_cols']) if c != group_u]
                    subgroup_u = st.selectbox("Secondary Color / Split:", subgroup_opts, index=0, key="u_subgroup")
                    
                color_arg = None if subgroup_u == "None" else subgroup_u
                fig_u_dist = px.box(
                    df, x=group_u, y=metric_u, color=color_arg,
                    points="all",
                    title=f"Distribution of '{metric_u}' grouped by '{group_u}'",
                    template="plotly_white"
                )
                st.plotly_chart(fig_u_dist, use_container_width=True)
                
            with utab2:
                st.markdown("#### Subject / Athlete Leaderboard")
                sub_col = profile['subject_col'] or df.columns[0]
                col_rk1, col_rk2 = st.columns([1, 1])
                with col_rk1:
                    rank_metric = st.selectbox("Rank by Metric:", profile['num_cols'], index=0, key="u_rank_metric")
                with col_rk2:
                    top_n = st.slider("Number of top subjects to display:", 5, min(len(df), 50), min(len(df), 15))
                    
                sorted_df = df.groupby(sub_col)[rank_metric].mean().reset_index().sort_values(by=rank_metric, ascending=False).head(top_n)
                fig_rank = px.bar(
                    sorted_df, x=sub_col, y=rank_metric,
                    color=rank_metric,
                    color_continuous_scale="Viridis",
                    title=f"Top {top_n} by {rank_metric}",
                    template="plotly_white"
                )
                st.plotly_chart(fig_rank, use_container_width=True)
                
            with utab3:
                st.markdown("#### Normalized Multi-Metric Radar Profile")
                sub_col = profile['subject_col'] or df.columns[0]
                if len(profile['num_cols']) >= 3:
                    subj_list = df[sub_col].dropna().unique().tolist()
                    selected_subj = st.selectbox("Select Subject to profile:", subj_list, key="u_radar_subj")
                    
                    # Radar metrics selection
                    radar_metrics = st.multiselect("Metrics to include in Radar:", profile['num_cols'], default=profile['num_cols'][:8])
                    if len(radar_metrics) >= 3:
                        subj_df = df[df[sub_col] == selected_subj]
                        subj_means = subj_df[radar_metrics].mean()
                        
                        # Percentile ranks across cohort
                        pct_df = df[radar_metrics].rank(pct=True) * 100
                        subj_pcts = [pct_df.loc[df[sub_col] == selected_subj, m].mean() for m in radar_metrics]
                        
                        fig_u_radar = go.Figure()
                        fig_u_radar.add_trace(go.Scatterpolar(
                            r=subj_pcts + [subj_pcts[0]],
                            theta=radar_metrics + [radar_metrics[0]],
                            fill='toself',
                            name=f"Subject: {selected_subj}",
                            line=dict(color='#00CC96', width=2)
                        ))
                        # Median reference
                        fig_u_radar.add_trace(go.Scatterpolar(
                            r=[50] * (len(radar_metrics) + 1),
                            theta=radar_metrics + [radar_metrics[0]],
                            name="Cohort Median (50th percentile)",
                            line=dict(color='#FFA15A', dash='dot')
                        ))
                        fig_u_radar.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                            showlegend=True,
                            title=f"Subject Multi-Metric Performance Profile ({selected_subj})"
                        )
                        st.plotly_chart(fig_u_radar, use_container_width=True)
                    else:
                        st.info("Please select at least 3 numeric metrics to render a radar profile.")
                else:
                    st.info("Dataset requires at least 3 numeric columns to generate a multi-metric radar profile.")
                    
            with utab4:
                col_tr1, col_tr2, col_tr3 = st.columns(3)
                with col_tr1:
                    x_trend = st.selectbox("X Axis (Predictor / Independent):", profile['num_cols'], index=0, key="u_xtrend")
                with col_tr2:
                    y_trend = st.selectbox("Y Axis (Response / Dependent):", profile['num_cols'], index=min(1, len(profile['num_cols'])-1), key="u_ytrend")
                with col_tr3:
                    trend_col = st.selectbox("Color Group:", ["None"] + (profile['group_candidates'] or profile['cat_cols']), key="u_trendcol")
                    
                trend_color_arg = None if trend_col == "None" else trend_col
                fig_trend = px.scatter(
                    df, x=x_trend, y=y_trend, color=trend_color_arg,
                    trendline="ols",
                    marginal_x="box", marginal_y="box",
                    title=f"Bivariate Analysis: {x_trend} vs {y_trend}",
                    template="plotly_white"
                )
                st.plotly_chart(fig_trend, use_container_width=True)
                
            with utab5:
                if len(profile['num_cols']) > 1:
                    corr_mat = df[profile['num_cols']].corr().round(2)
                    fig_mat = px.imshow(corr_mat, text_auto=True, color_continuous_scale="Spectral_r", aspect="auto", title="Comprehensive Correlation Heatmap")
                    st.plotly_chart(fig_mat, use_container_width=True)
                else:
                    st.info("Not enough numeric columns for correlation matrix.")
                    
            with utab6:
                st.markdown("#### 🛠️ Custom Chart Studio")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    c_type = st.selectbox("Chart Type", ["Scatter", "Box", "Bar", "Histogram"], key="u_c_type")
                with c2:
                    x_col = st.selectbox("X Axis", df.columns, index=0, key="u_c_x")
                with c3:
                    y_col = st.selectbox("Y Axis", profile['num_cols'], index=0, key="u_c_y")
                with c4:
                    color_col = st.selectbox("Color / Group", ["None"] + profile['cat_cols'], key="u_c_color")
                col_p = None if color_col == "None" else color_col
                if c_type == "Scatter":
                    st.plotly_chart(px.scatter(df, x=x_col, y=y_col, color=col_p, template="plotly_white"), use_container_width=True)
                elif c_type == "Box":
                    st.plotly_chart(px.box(df, x=x_col, y=y_col, color=col_p, template="plotly_white"), use_container_width=True)
                elif c_type == "Bar":
                    st.plotly_chart(px.bar(df, x=x_col, y=y_col, color=col_p, template="plotly_white"), use_container_width=True)
                else:
                    st.plotly_chart(px.histogram(df, x=y_col, color=col_p, template="plotly_white"), use_container_width=True)

    # -------------------------------------------------------------
    # TAB 3: TAILORED AI ASSESSMENT (ADAPTIVE FOR ANY DATASET)
    # -------------------------------------------------------------
    with tab3:
        st.subheader("🤖 AI Clinical & Sports Performance Assessment")
        st.caption(f"Adaptive Prompt automatically tuned for: **{profile['type']}**")
        
        ai_prompt = st.text_area(
            "System Instruction for the AI:", 
            value=profile['default_prompt'],
            height=140
        )
            
        if st.button("🚀 Generate AI Report", type="primary"):
            stats_content = st.session_state.get('stats_text', '')
            if not stats_content:
                st.error("No statistics available. Please check the Data tab.")
            else:
                with st.spinner(f"Analyzing {profile['type']} using {model_name}..."):
                    try:
                        full_prompt = (
                            f"{ai_prompt}\n\n"
                            f"Dataset: {selected_file.name} ({profile['type']})\n\n"
                            f"Here are the computed descriptive & grouped statistics:\n\n"
                            f"{stats_content}"
                        )
                        
                        response = ollama.chat(
                            model=model_name,
                            messages=[{
                                'role': 'user',
                                'content': full_prompt
                            }],
                            options={
                                "num_ctx": ctx_size,
                                "num_predict": max_tokens,
                                "temperature": temperature,
                            }
                        )
                        
                        msg = response.get('message', {})
                        content = msg.get('content', '')
                        thinking = msg.get('thinking', '')
                        
                        if thinking and thinking.strip():
                            with st.expander("🤔 Diagnostic Process"):
                                st.markdown(thinking)
                                
                        if content and content.strip():
                            st.success("✅ Assessment complete")
                            st.markdown(content)
                            st.download_button(
                                "📥 Download Report (.md)",
                                data=content,
                                file_name=f"Report_{selected_file.stem}.md",
                                mime="text/markdown"
                            )
                        else:
                            st.warning("Empty response from the model.")
                            
                    except Exception as e:
                        err_str = str(e)
                        st.error(f"Error during AI analysis: {err_str}")
                        if "failed to allocate" in err_str.lower() or "cuda_host" in err_str.lower():
                            st.warning(
                                "💡 **Out of Memory Notice**: The model is requiring more RAM than currently available. "
                                "In the sidebar, try selecting a lighter model (e.g., a 3B or 1.5B model like `llama3.2:3b` or `qwen2.5:3b`) "
                                "or reducing the Context Size slider."
                            )