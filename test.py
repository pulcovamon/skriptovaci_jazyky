import os
import random
import string
from enum import Enum
import subprocess
import shutil


class Extension(Enum):
    TXT="txt"
    JSON="json"
    CSV="csv"
    XML="xml"
    PY="py"
    

class BashScriptTester:
    
    def __init__(self, bash_script_path, location):
        self.bash_script_path = bash_script_path
        self.location = location
        
    def _initialize_variables(self):
        self.extensions = {}
        self.max_depth = 0
        self.number_of_directories = 1
        self.number_of_files = 0
        self.sum_of_sizes = 0
        self.average_size = 0
        self.largest_size = 0
        self.sizes = []
        self.median_size = 0
        
    def _generate_directory(self, location):
        name = "".join(random.choices(string.ascii_letters, k=random.randint(1, 10)))
        while os.path.exists(os.path.join(location, name)):
            name = "".join(random.choices(string.ascii_letters, k=random.randint(1, 10)))
        os.mkdir(os.path.join(location, name))
        self.number_of_directories += 1
        return name
                
    def _generate_file(self, location):
        name = "".join(random.choices(string.ascii_letters, k=random.randint(1, 10)))
        extension = random.choice(list(Extension)).value
        name = f"{name}.{extension}"
        path = os.path.join(location, name)
        with open(path, "w") as file:
            for _ in range(random.randint(1, 50)):
                file.write("".join(random.choices(string.ascii_letters + string.digits, k=random.randint(1, 20))))
        self.number_of_files += 1
        size = os.path.getsize(path)
        self.sum_of_sizes += size
        self.largest_size = size if size > self.largest_size else self.largest_size
        self.sizes.append(size)
        self.extensions[extension] = (1, size) if extension not in self.extensions.keys() else (self.extensions[extension][0]+1, self.extensions[extension][1]+size)
        return name
                
    def _generate(self, location, depth, files=True):
        if depth > 0:
            name = self._generate_directory(location)
            self._generate(os.path.join(location, name), depth=depth-1, files=files)
            if files:
                for _ in range(random.randint(1, 3)):
                    function = random.choice([self._generate_directory, self._generate_file])
                    name = function(location)
                    if function == self._generate_directory:
                        self._generate(os.path.join(location, name), depth=depth-1)
                self._generate_file(location)
    
    
    def _median_size(self):
        if len(self.sizes) == 1:
            return self.sizes[0]
        if len(self.sizes) == 2:
            return int((self.sizes[0] + self.sizes[1]) / 2)
        sorted_sizes = self.sizes.copy()
        sorted_sizes.sort()
        if len(self.sizes) % 2 == 0:
            return int((sorted_sizes[int((len(sorted_sizes))/2)] + sorted_sizes[int((len(sorted_sizes))/2+1)]) / 2)
        return int(sorted_sizes[int(len(sorted_sizes)/2)])
    
    
    def _parse_and_check_output(self, output):
        extensions = set()
        current_ext = None
        for line in output.split(b'\n'):
            line = str(line)[2 : -1].strip()
            if line == "" or "Files info" in line or "Directories info" in line:
                continue
            if "Max depth" in line:
                assert line.split(":")[-1].strip() == str(self.max_depth)
            elif "Number of directories" in line:
                assert line.split(":")[-1].strip() == str(self.number_of_directories)
            elif "Average number of file per directory" in line:
                assert line.split(":")[-1].strip() == str(int(self.number_of_files / self.number_of_directories))
            elif "Number of files" in line:
                assert line.split(":")[-1].strip() == str(self.number_of_files)
            elif "The largest size" in line:
                assert line.split(":")[-1].strip() == str(self.largest_size)
            elif "Average size" in line:
                assert line.split(":")[-1].strip() == str(int(self.sum_of_sizes / self.number_of_files))
            elif "Median size" in line:
                assert line.split(":")[-1].strip() == str(self._median_size())
            elif "Extension" in line:
                current_ext = line.split(" ")[1].strip()
                extensions.add(current_ext)
            elif "number of files" in line:
                assert line.split(":")[-1].strip() == str(self.extensions[current_ext][0])
            elif "overall size of files" in line:
                assert line.split(":")[-1].strip() == str(self.extensions[current_ext][1])
        assert extensions == set(self.extensions.keys())
                    
                    
    def test_deep_directories(self):
        print("test deep directories")
        path = os.path.join(self.location, "deep_tree_structure")
        self._initialize_variables()
        os.mkdir(path)
        self.max_depth = 5
        self._generate(path, 5)
        print("directory structure generation finished")
        process = subprocess.Popen(["./directory-statistics.sh", "-p", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("script executed")
        output, error = process.communicate()
        assert error == b''
        self._parse_and_check_output(output)
        
        
    def test_shallow_directories(self):
        print("test shallow directories")
        path = os.path.join(self.location, "shallow_tree_structure")
        self._initialize_variables()
        os.mkdir(path)
        self.max_depth = 1
        self._generate(path, 1)
        print("directory structure generation finished")
        process = subprocess.Popen(["./directory-statistics.sh", "-p", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("script executed")
        output, error = process.communicate()
        assert error == b''
        self._parse_and_check_output(output)

        
    def test_empty_directory(self):
        print("test empty directory")
        path = os.path.join(self.location, "empty")
        os.mkdir(path)
        process = subprocess.Popen(["./directory-statistics.sh", "-p", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("script executed")
        output, error = process.communicate()
        assert error == b''
        assert "Parent directory does not contain any files" in str(output)
        assert "Max depth: 0" in str(output)
        
        
    def test_help(self):
        print("test help flag")
        process = subprocess.Popen(["./directory-statistics.sh", "-h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("script executed")
        output, error = process.communicate()
        assert error == b''
        assert "  -h   Show this help message" in str(output)
        assert "  -p   Specify the parent directory" in str(output)
        
        
    def test_wrong_flag(self):
        print("test wrong flag")
        process = subprocess.Popen(["./directory-statistics.sh", "-x"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("script executed")
        output, error = process.communicate()
        assert output == b''
        assert "Wrong flag" in str(error)
        
        
    def test_wrong_path(self):
        print("test wrong path")
        path = os.path.join(self.location, "uiguiygyiug")
        process = subprocess.Popen(["./directory-statistics.sh", "-p", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("script executed")
        output, error = process.communicate()
        assert output == b''
        assert f"Directory {path} does not exist" in str(error)
    
    
    def test_just_directories(self):
        print("test only directories")
        path = os.path.join(self.location, "just_directories")
        self._initialize_variables()
        os.mkdir(path)
        self.max_depth = 2
        self._generate(path, 2, files=False)
        print("directory structure generation finished")
        process = subprocess.Popen(["./directory-statistics.sh", "-p", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("script executed")
        output, error = process.communicate()
        assert error == b''
        print(output)
        assert "Parent directory does not contain any files" in str(output)
        assert "Max depth: 2" in str(output)
        
if __name__ == "__main__":
    path = "/home/monika/Documents/fbmi/SKJ/semestralka/test_directory"
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except:
            print("directory cannot be deleted, please remove it manualy and then run program again")
            exit()
    os.mkdir(path)
    tester = BashScriptTester("/home/monika/Documents/fbmi/SKJ/semestralka/directory-statistics.sh",
                              path)
    
    tester.test_deep_directories()
    tester.test_shallow_directories()
    tester.test_empty_directory()
    tester.test_just_directories()
    tester.test_help()
    tester.test_wrong_flag()
    tester.test_wrong_path()
    
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except:
            print("directory cannot be deleted, please remove it manualy")