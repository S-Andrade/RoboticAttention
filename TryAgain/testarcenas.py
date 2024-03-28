from langchain.document_loaders import WikipediaLoader
from langchain.text_splitter import TokenTextSplitter
from langchain.document_loaders import PyPDFLoader
import docx

def getText(filename):
    doc = docx.Document(filename)
    doc.page_content()
    fullText = []
    f = open("hiddenprofiles.txt","a", encoding="utf8")
    for para in doc.paragraphs:
        fullText.append(para.text)
        f.write(para.text)
    f.close()
    #return '\n'.join(fullText)

#getText("C:\\Users\\sandr\\Desktop\\HiddenProfiles\\NoCriticalInfo-A.docx")
#with open("hiddenprofiles.txt", encoding="utf8") as f:
#    state_of_the_union = f.read()



#loader = PyPDFLoader("NoCriticalInfo-A.pdf")
#docs = loader.load_and_split()

# Read the wikipedia article
raw_documents = WikipediaLoader(query="Walt Disney").load()
print(raw_documents)
# Define chunking strategy
#text_splitter = TokenTextSplitter(chunk_size=2048, chunk_overlap=24)

# Only take the first the raw_documents
#documents = text_splitter.split_documents(docs)

#print(documents[0])