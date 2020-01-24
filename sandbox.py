import streamlit as st

name = st.text_input("Enter your name:")
age = st.slider("Your age:", min_value=10, max_value=100)

st.write(f"Hi, ", name, " you are ", age, "years old.")

slider = st.empty()
value = slider.slider("test", min_value=0, max_value=10,)

# slider.value = 8

st.write(dir(slider))

st.write(value)

