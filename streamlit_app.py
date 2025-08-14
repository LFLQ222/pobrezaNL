import streamlit as st

def main():
    st.set_page_config(
        page_title="Pobreza Multidimensional NL 2024",
        page_icon="📊",
        layout="wide"
    )
    
    # Main title in orange
    st.markdown(
        '<h1 style="color: #FF8C00; text-align: center;">Pobreza multidimensional Nuevo León 2024</h1>',
        unsafe_allow_html=True
    )
    
    # Figma iframe
    st.markdown("""
    <div style="display: flex; justify-content: center; margin: 20px 0;">
        <iframe style="border: 1px solid rgba(0, 0, 0, 0.1);" width="1000" height="600" 
                src="https://embed.figma.com/slides/SOM54LTW7AH1ETRTfA2FAa/Pobreza-2024-NL-INFORMA?node-id=4005-830&embed-host=share" 
                allowfullscreen>
        </iframe>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
