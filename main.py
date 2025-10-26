from utils import read_cvs, clean_and_preprocess

def main():
    cvs = read_cvs("DataSet")

    # Apply preprocessing
    for person, files in cvs.items():
        for fmt, content in files.items():
            cvs[person][fmt] = clean_and_preprocess(content)

    # Example output
    print(f"Processed {len(cvs)} candidates:")
    for name in cvs:
        print(f"- {name} ({', '.join(cvs[name].keys())})")

if __name__ == "__main__":
    main()
