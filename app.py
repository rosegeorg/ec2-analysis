import streamlit as st
import pandas as pd
import plotly.express as px

st.title("EC2 Instance EDA Dashboard")

df = pd.read_csv("ec2dataset.csv")

st.write("Dataset Preview")
st.dataframe(df)

# display dataset info
st.subheader("Dataset Information")
col1, col2, col3 = st.columns(3)
col1.metric("Number of Instances", len(df))
col2.metric("Number of Columns", len(df.columns))
col3.metric("Missing Values", df.isna().sum().sum())

# examine the dataset
st.subheader("Dataset Structure")
st.write("Columns:")
st.write(df.columns.tolist())

st.subheader("Data Types")
st.write(df.dtypes.astype(str))

df["Memory_GiB"] = (
    df["Instance Memory"]
    .str.extract(r"([\d.]+)")
    .astype(float)
)

df["vCPU_Count"] = (
    df["vCPUs"]
    .str.extract(r"(\d+)")
    .astype(float)
)

def clean_price(value):
    if pd.isna(value):
        return None

    value = str(value)

    if "unavailable" in value.lower():
        return None

    return float(
        value.replace("$", "")
        .replace(" hourly", "")
        .strip()
    )

price_columns = [
    "On Demand",
    "Linux Reserved cost",
    "Linux Spot Minimum cost",
    "Windows On Demand cost",
    "Windows Reserved cost"
]

for column in price_columns:
    df[column + "_USD"] = df[column].apply(clean_price)
df["Monthly_On_Demand"] = df["On Demand_USD"] * 730

st.subheader("Monthly On-Demand Cost")

st.dataframe(
    df[
        [
            "Name",
            "API Name",
            "Memory_GiB",
            "vCPU_Count",
            "On Demand_USD",
            "Monthly_On_Demand"
        ]
    ]
)

#add an instance filter
st.sidebar.header("Filters")

max_memory = float(df["Memory_GiB"].max())

memory_filter = st.sidebar.slider(
    "Maximum Memory (GiB)",
    min_value=0.5,
    max_value=max_memory,
    value=max_memory
)

# add vCPU filtering
cpu_values = sorted(
    df["vCPU_Count"].dropna().unique()
)

selected_cpu = st.sidebar.multiselect(
    "vCPU Count",
    options=cpu_values,
    default=cpu_values
)

# add network filtering
network_values = sorted(
    df["Network Performance"].dropna().unique()
)

selected_network = st.sidebar.multiselect(
    "Network Performance",
    options=network_values,
    default=network_values
)

# add storage filtering
storage_values = sorted(
    df["Instance Storage"].dropna().unique()
)

selected_storage = st.sidebar.multiselect(
    "Instance Storage",
    options=storage_values,
    default=storage_values
)
max_hourly_price = float(df["On Demand_USD"].max())

price_filter = st.sidebar.slider(
    "Maximum Hourly Price",
    min_value=0.0,
    max_value=max_hourly_price,
    value=max_hourly_price
)
max_monthly_cost = float(df["Monthly_On_Demand"].max())

monthly_cost_filter = st.sidebar.slider(
    "Maximum Monthly Cost",
    min_value=0.0,
    max_value=max_monthly_cost,
    value=max_monthly_cost
)

filtered_df = df[
    (df["Memory_GiB"] <= memory_filter) &
    (df["vCPU_Count"].isin(selected_cpu)) &
    (df["Network Performance"].isin(selected_network)) &
    (df["Instance Storage"].isin(selected_storage)) &
    (df["On Demand_USD"] <= price_filter) &
    (df["Monthly_On_Demand"] <= monthly_cost_filter)
]

# Challenge 5 - Memory per vCPU
filtered_df = filtered_df.copy()

filtered_df["Memory_per_vCPU"] = (
    filtered_df["Memory_GiB"] /
    filtered_df["vCPU_Count"]
)

st.subheader("Highest Memory per vCPU")

memory_per_cpu = (
    filtered_df
    .sort_values(
        "Memory_per_vCPU",
        ascending=False
    )
    [
        [
            "Name",
            "API Name",
            "Memory_GiB",
            "vCPU_Count",
            "Memory_per_vCPU"
        ]
    ]
    .head(15)
)

st.dataframe(memory_per_cpu)

st.subheader("Filtered EC2 Instances")
st.write(f"{len(filtered_df)} instances found")
st.dataframe(filtered_df)

#creater KPI card
st.subheader("EC2 Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Instances",
    len(filtered_df)
)

col2.metric(
    "Avg Memory",
    f"{filtered_df['Memory_GiB'].mean():.2f} GiB"
)

col3.metric(
    "Avg vCPUs",
    f"{filtered_df['vCPU_Count'].mean():.1f}"
)

col4.metric(
    "Avg Hourly Cost",
    f"${filtered_df['On Demand_USD'].mean():.4f}"
)

#memory distribution chart
st.subheader("Memory Distribution")

fig = px.histogram(
    filtered_df,
    x="Memory_GiB",
    nbins=30,
    title="Distribution of EC2 Memory"
)

st.plotly_chart(fig, use_container_width=True)

#vCpu distribution
st.subheader("vCPU Distribution")

fig = px.histogram(
    filtered_df,
    x="vCPU_Count",
    title="Distribution of vCPUs"
)

st.plotly_chart(fig, use_container_width=True)

#memory vs vCPU
st.subheader("Memory vs vCPUs")

fig = px.scatter(
    filtered_df,
    x="vCPU_Count",
    y="Memory_GiB",
    hover_name="API Name",
    hover_data=["On Demand_USD"],
    title="EC2 Memory vs vCPU"
)

st.plotly_chart(fig, use_container_width=True)

#memory vs cost
st.subheader("Memory vs On-Demand Cost")

fig = px.scatter(
    filtered_df,
    x="Memory_GiB",
    y="On Demand_USD",
    hover_name="API Name",
    size="vCPU_Count",
    title="Memory vs EC2 On-Demand Cost"
)

st.plotly_chart(fig, use_container_width=True)

#Finding cheapest EC2 Instance
st.subheader("Lowest-Cost EC2 Instances")

cheapest = (
    filtered_df
    .sort_values("On Demand_USD")
    [
        [
            "Name",
            "API Name",
            "Memory_GiB",
            "vCPU_Count",
            "On Demand_USD",
            "Monthly_On_Demand"
        ]
    ]
    .head(10)
)

st.dataframe(cheapest)

#most expensive ec2 instance
st.subheader("Highest-Cost EC2 Instances")

most_expensive = (
    filtered_df
    .sort_values(
        "On Demand_USD",
        ascending=False
    )
    [
        [
            "Name",
            "API Name",
            "Memory_GiB",
            "vCPU_Count",
            "On Demand_USD",
            "Monthly_On_Demand"
        ]
    ]
    .head(10)
)

st.dataframe(most_expensive)

#Compare pricing models
pricing = filtered_df[
    [
        "Name",
        "API Name",
        "On Demand_USD",
        "Linux Reserved cost_USD",
        "Linux Spot Minimum cost_USD",
        "Windows On Demand cost_USD",
        "Windows Reserved cost_USD"
    ]
]

st.subheader("EC2 Pricing Comparison")

st.dataframe(pricing)

#pricing model chart
selected_instance = st.selectbox(
    "Select an EC2 Instance",
    filtered_df["API Name"].unique()
)
instance = filtered_df[
    filtered_df["API Name"] == selected_instance
].iloc[0]
pricing_data = pd.DataFrame({
    "Pricing Model": [
        "On Demand",
        "Linux Reserved",
        "Linux Spot"
    ],
    "Hourly Cost": [
        instance["On Demand_USD"],
        instance["Linux Reserved cost_USD"],
        instance["Linux Spot Minimum cost_USD"]
    ]
})
fig = px.bar(
    pricing_data,
    x="Pricing Model",
    y="Hourly Cost",
    title=f"Pricing Comparison: {selected_instance}"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

#part 20 calsulate monthly pricing
pricing_data["Monthly Cost"] = (
    pricing_data["Hourly Cost"] * 730
)

st.dataframe(pricing_data)

#part-21 create a cost efficiency metric 
df["Cost_Per_GiB"] = (
    df["On Demand_USD"] /
    df["Memory_GiB"]
)
filtered_df["Cost_Per_GiB"] = (
    filtered_df["On Demand_USD"] /
    filtered_df["Memory_GiB"]
)
st.subheader("Cost per GiB of Memory")

efficiency = (
    filtered_df
    .sort_values("Cost_Per_GiB")
    [
        [
            "Name",
            "API Name",
            "Memory_GiB",
            "vCPU_Count",
            "On Demand_USD",
            "Cost_Per_GiB"
        ]
    ]
    .head(15)
)

st.dataframe(efficiency)

#add a download button
csv = filtered_df.to_csv(index=False)

st.download_button(
    label="Download Filtered Dataset",
    data=csv,
    file_name="filtered_ec2_instances.csv",
    mime="text/csv"
)

# PART 2 - REGRESSION ANALYSIS

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

st.header("EC2 Cost Prediction Using Regression")

# Prepare data
regression_df = df.dropna(
    subset=["Memory_GiB", "vCPU_Count", "On Demand_USD"]
)

X = regression_df[["Memory_GiB", "vCPU_Count"]]
y = regression_df["On Demand_USD"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
from sklearn.linear_model import Ridge
import numpy as np

# Train model using log-transformed costs
model = Ridge(alpha=10.0)
model.fit(X_train, np.log(y_train.clip(lower=0.000001)))
# Step 7 - Evaluate the Model

from sklearn.metrics import mean_absolute_error, mean_squared_error

st.subheader("Step 7: Model Evaluation")

y_pred = np.exp(model.predict(X_test))

mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = mse ** 0.5

col1, col2, col3 = st.columns(3)

col1.metric("MAE", f"{mae:.4f}")
col2.metric("MSE", f"{mse:.4f}")
col3.metric("RMSE", f"{rmse:.4f}")


# Step 8 - Visualize the Results

st.subheader("Step 8: Actual vs Predicted Costs")

fig = px.scatter(
    x=y_test,
    y=y_pred,
    labels={
        "x": "Actual On-Demand Cost ($/hour)",
        "y": "Predicted On-Demand Cost ($/hour)"
    },
    title="Actual vs Predicted EC2 Costs"
)

# Add perfect prediction reference line
min_value = min(y_test.min(), y_pred.min())
max_value = max(y_test.max(), y_pred.max())

fig.add_scatter(
    x=[min_value, max_value],
    y=[min_value, max_value],
    mode="lines",
    name="Perfect Prediction",
    line=dict(color="red", dash="dash")
)

st.plotly_chart(fig, use_container_width=True)
# Step 9 - Make Predictions

st.subheader("Predict EC2 Instance Cost")

new_instance = pd.DataFrame(
    [[6, 2]],
    columns=["Memory_GiB", "vCPU_Count"]
)

predicted_cost = np.exp(model.predict(new_instance))[0]

st.success(
    f"Predicted On-Demand Cost: ${predicted_cost:.6f}/hour"
)
