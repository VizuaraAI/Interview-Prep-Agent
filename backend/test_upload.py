import requests
import json

def test_resume_upload():
    """Test resume upload endpoint"""

    # Path to the test resume
    resume_path = "/Users/rajat/Desktop/Vizuara RAG Demo Nutri Chatbot/Himanshu Kumar Resume - Himanshu Kumar.pdf"

    url = "http://localhost:8000/upload-resume"

    print("Testing resume upload...")
    print(f"Uploading: {resume_path}")

    try:
        with open(resume_path, 'rb') as f:
            files = {'file': ('resume.pdf', f, 'application/pdf')}
            response = requests.post(url, files=files)

        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS! Resume uploaded and processed.")
            print("\n📋 Extracted Data:")
            print("\n👤 Contact Info:")
            print(json.dumps(data['contact_info'], indent=2))
            print("\n📚 Sections Extracted:")
            for section, content in data['sections'].items():
                print(f"\n{section}:")
                print(f"  Content Length: {len(content)} characters")
                print(f"  Preview: {content[:200]}...")

            print(f"\n💾 Student ID: {data['student_id']}")

            return data['student_id']

        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            return None

    except FileNotFoundError:
        print(f"❌ Error: Resume file not found at {resume_path}")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend. Make sure it's running at http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_get_student(student_id):
    """Test get student endpoint"""

    url = f"http://localhost:8000/student/{student_id}"

    print(f"\n\nTesting student retrieval for ID: {student_id}")

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS! Student data retrieved.")
            print("\n👤 Student Info:")
            print(json.dumps(data['student'], indent=2))
            print("\n📚 Sections:")
            for section, content in data['sections'].items():
                print(f"\n{section}:")
                print(f"  Length: {len(content)} characters")

        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("PART 1 TEST: Resume Upload and Extraction")
    print("=" * 60)

    student_id = test_resume_upload()

    if student_id:
        test_get_student(student_id)

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
