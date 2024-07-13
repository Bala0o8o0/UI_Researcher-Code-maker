import sys
import time
import streamlit as st
from crewai import Agent, Task, Crew, Process
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import Tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debugging: Print the API key to ensure it's loaded correctly
groq_api_key = os.getenv("GROQ_API_KEY")
# print("GROQ_API_KEY:", groq_api_key)

if not groq_api_key:
    os.environ["GROQ_API_KEY"] = "your_actual_api_key_here"
    groq_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model='llama3-8b-8192',
    api_key=os.getenv("GROQ_API_KEY"),  # Get the API key from the .env file
)

duckduckgo_search = DuckDuckGoSearchRun()

# to keep track of tasks performed by agents
task_values = []

def create_crewai_setup(product_name):
    # Define Agents
    ui_researcher = Agent(
        role="UI Researcher",
        goal=f"""Research the latest UI trends for {product_name} and 
                 suggest design improvements""",
        backstory=f"""Expert in user interface design and user experience. 
                      Skilled in identifying the latest trends and best practices 
                      in UI design.""",
        verbose=True,
        allow_delegation=True,
        tools=[duckduckgo_search],
        llm=llm,
    )

    code_maker = Agent(
        role="Code Maker",
        goal=f"Generate code snippets for {product_name} based on the requirements",
        backstory=f"""Experienced software developer with a knack for writing 
                      clean and efficient code. Specializes in generating 
                      code snippets for various applications.""",
        verbose=True,
        allow_delegation=True,
        llm=llm,
    )

    # Define Tasks
    task1 = Task(
        description=f"""Research the latest UI trends for {product_name}. 
                    Write a report suggesting design improvements. 
                    Include at least 10 bullet points on key UI trends.""",
        expected_output="Report on UI trends and design improvements.",
        agent=ui_researcher,
    )
    task2 = Task(
        description=f"""Generate code snippets for {product_name} based on the requirements. 
                    Include at least 10 code snippets addressing key functionalities.""",
        expected_output="Code snippets for key functionalities.",
        agent=code_maker,
    )

    # Create and Run the Crew
    product_crew = Crew(
        agents=[ui_researcher, code_maker],
        tasks=[task1, task2],
        verbose=2,
        process=Process.sequential,
    )

    crew_result = product_crew.kickoff()
    return crew_result

# Display the console processing on streamlit UI
class StreamToExpander:
    def __init__(self, expander):
        self.expander = expander
        self.buffer = []
        self.colors = ['red', 'green', 'blue', 'orange']  # Define a list of colors
        self.color_index = 0  # Initialize color index

    def write(self, data):
        # Filter out ANSI escape codes using a regular expression
        cleaned_data = re.sub(r'\x1B\[[0-9;]*[mK]', '', data)

        # Check if the data contains 'task' information
        task_match_object = re.search(r'\"task\"\s*:\s*\"(.*?)\"', cleaned_data, re.IGNORECASE)
        task_match_input = re.search(r'task\s*:\s*([^\n]*)', cleaned_data, re.IGNORECASE)
        task_value = None
        if task_match_object:
            task_value = task_match_object.group(1)
        elif task_match_input:
            task_value = task_match_input.group(1).strip()

        if task_value:
            st.toast(":robot_face: " + task_value)

        # Check if the text contains the specified phrase and apply color
        if "Entering new CrewAgentExecutor chain" in cleaned_data:
            # Apply different color and switch color index
            self.color_index = (self.color_index + 1) % len(self.colors)  # Increment color index and wrap around if necessary

            cleaned_data = cleaned_data.replace("Entering new CrewAgentExecutor chain", f":{self.colors[self.color_index]}[Entering new CrewAgentExecutor chain]")

        if "UI Researcher" in cleaned_data:
            cleaned_data = cleaned_data.replace("UI Researcher", f":{self.colors[self.color_index]}[UI Researcher]")
        if "Code Maker" in cleaned_data:
            cleaned_data = cleaned_data.replace("Code Maker", f":{self.colors[self.color_index]}[Code Maker]")
        if "Finished chain." in cleaned_data:
            cleaned_data = cleaned_data.replace("Finished chain.", f":{self.colors[self.color_index]}[Finished chain.]")

        self.buffer.append(cleaned_data)
        if "\n" in data:
            self.expander.markdown(''.join(self.buffer), unsafe_allow_html=True)
            self.buffer = []

# Streamlit interface
def run_crewai_app():
    st.title("Website UI Researcher & Code Maker")
    st.image("image.png")  # Ensure the path to the image is correct

    # Use st.header to create a header for 'About the Team'
    st.header("About the Team:")

    st.subheader("UI Researcher")
    st.text("""       
    
   - Research the latest UI trends and suggest design improvements
   - Expert in user interface design and user experience. 
            Skilled in identifying the latest trends and 
            best practices in UI design.""")

    st.subheader("Code Maker")
    st.text("""       
   
    -Generate code snippets based on the requirements
    -Experienced software developer with a knack for 
            writing clean and efficient code. 
            Specializes in generating 
    code snippets for various applications.
    -The code generated by code maker is not Ready for production """)

    product_name = st.text_input("Enter.")

    if st.button("Run Researcher/Coder"):
        # Placeholder for stopwatch
        stopwatch_placeholder = st.empty()
        
        # Start the stopwatch
        start_time = time.time()
        with st.expander("Processing!"):
            sys.stdout = StreamToExpander(st)
            with st.spinner("Generating Results"):
                crew_result = create_crewai_setup(product_name)

        # Stop the stopwatch
        end_time = time.time()
        total_time = end_time - start_time
        stopwatch_placeholder.text(f"Total Time Elapsed: {total_time:.2f} seconds")

        st.header("Results:")
        st.markdown(crew_result)

if __name__ == "__main__":
    run_crewai_app()
