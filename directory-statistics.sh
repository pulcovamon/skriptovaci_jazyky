#!/bin/bash

# Rekurzivne prochazi adresarovou strukturu
function search_directories() {
    # argument funkce cislo 1
    local directory="$1"

    local depth
    # vygrepuje vsechny / z cesty a spocte pocet radku => hloubka adresare
    depth=$(grep -o "/" <<< "$directory" | wc -l)
    # -gt je greater than (>)
    if [ "$((depth - inicial_depth))" -gt "$max_depth" ]; then
        max_depth="$((depth - inicial_depth))"
    fi
    
    for item in "$directory"/*; do
        # pokud item je soubor (-f), takze se zjisti velikosti, zvysi se pocet souboru o 1
        if [ -f "$item" ]; then
            # du zjisti velikost souboru, -b v bytech
            # awk vezme ten vystup a vytahne z nej prvni sloupec, coz je velikost v bytech (druhy sloupec je nazev souboru)
            size=$(du -b "$item" | awk '{print $1}')
            sizes+=("$size")
            sum_size=$((sum_size + size))
            ((number_of_files++))
            if [ "$size" -gt "$largest_size" ]; then
                largest_size="$size"
            fi
            # zjisti se pripona a prida se do listu
            # vytiskne cestu k souboru, tu preda awk
            # -F . nastavi oddelovac na . takze rozdeli radek na to pred . a za . a da do pole
            # pak vytiskne posledni element z pole pro kazdy radek (ten je tady jen jeden)
            extension=$(echo "$item" | awk -F . '{print $NF}')
            if [[ -n "$extension" && ! -d "$item" ]]; then
                ((extensions_count[$extension]++))
                extensions_sizes[$extension]=$((extensions_sizes[$extension] + size))
            fi
        # pokud item je adresar (-d), takze se zvysi pocet adresaru o 1 a zavola se rekurzivne funkce
        elif [ -d "$item" ]; then
            number_of_directories=$((number_of_directories + 1))
            search_directories "$item"
        fi
    done
}

# vypocet medianu, v argumentu bere pole "sizes"
function median() {
    # argument funkce, da to do pole vsechny argumenty
    local sizes=("$@")
    local sorted_sizes=()
    # razeni pole a ulozeni do promenne "sorted_file"
    # mapfile nacte vstupni hodnoty (serazene hodnoty) do pole, -t odstrani newliny
    # printf adt vystiskne vsechny hodnoty pole, kazdou na novy radek
    # ISF je internal field separator, tady se to nastavilo na newline a unset to vrati, aby to neovlivnilo dalsi
    mapfile -t sorted_sizes < <(printf '%s\n' "${sizes[@]}" | sort -n); unset IFS
    local median
    # pro sudy pocet prvku se udela prumer z dvou prostrednich prvku pole
    # "#" spocita delku, "@" je pro vsechnt prvky
    if (( ${#sizes[@]} ==  1 )); then
        median=$(( sorted_sizes[0] ))
    elif (( ${#sizes[@]} ==  2 )); then
        median=$(( (sorted_sizes[0] + sorted_sizes[1]) / 2))
    elif (( ${#sizes[@]} % 2 == 0 )); then
        local index1=$(( (${#sorted_sizes[@]}) / 2 ))
        local index2=$(( (${#sorted_sizes[@]}) / 2 +1 ))
        median=$(( (sorted_sizes[index1] + sorted_sizes[index2]) / 2 ))
    # pro lichy pocet prvku se vezme prostredni prvek pole
    else
        local index=$(( (${#sorted_sizes[@]}) / 2 ))
        median="${sorted_sizes[index]}"

    fi
    # navratova hodnota
    echo "$median"
}

# getopts zpracovava flagy z prikazove radky
while getopts "hp:" opt; do
    case $opt in
        h)
            # vypise do stdout napovedu a ukonci skript bez erroru
            echo "Usage: $(basename "$0") -p <parent_directory>"
            echo "Options:"
            echo "  -h   Show this help message"
            echo "  -p   Specify the parent directory"
            exit 0
            ;;
        # ulozi argument do promenne, OPTARG obsahuje ten argument
        p) PARENT_DIR="$OPTARG";;
        # pokud je flag neznamy, vypise se hodnota do stderr, ukonci skript s errorem
        # "\" odescapuje "?", ktery tady znamena kterykoli jiny flag
        \?) echo "Wrong flag" >&2; exit 1;;
    esac
done

# shift posune argumenty tak, ze parent adresar bude prvni argument ktery neni flag
shift $((OPTIND -1))

# zjisti, jestli byla zadana cesta k parent adresari, pokud ne, vypise hlasku do stderr a ukonci skript s errorem
if [ -z "$PARENT_DIR" ]; then
    echo "Path to the parent directory is missing. Use flag -p." >&2
    exit 1
fi

# zjisti, jestli zadana cesta existuje a pokud ne, vypise hlasku do stderr a ukonci skript s errorem
if [ ! -d "$PARENT_DIR" ]; then
    echo "Directory $PARENT_DIR does not exist" >&2
    exit 1
fi

# deklarovani a inicializace globalnich promennych
declare -a sizes=()
largest_size=0
sum_size=0
number_of_files=0
number_of_directories=1
inicial_depth=$(grep -o "/" <<< "$PARENT_DIR" | wc -l)
max_depth=0
declare -A extensions_count
declare -A extensions_sizes

# volani rekurzivniho prochazeni adresarove struktury s parent adresarem jako argument
search_directories "$PARENT_DIR"

# zpracovani a zobrazeni vysledku na stdout
echo "Directories info:"
echo "  Max depth: $max_depth"
if [ "$number_of_files" -gt 0 ]; then
    average_number_of_sizes=$((number_of_files / number_of_directories))
    average=$((sum_size / number_of_files))
    median=$(median "${sizes[@]}")
    echo "  Number of directories: $number_of_directories"
    echo "  Average number of file per directory: $average_number_of_sizes"
    echo "  Number of files: $number_of_files"
    echo ""
    echo "Files info:"
    echo "  The largest size: $largest_size"
    echo "  Average size: $average"
    echo "  Median size: $median"
    echo ""
    for ext in "${!extensions_count[@]}"; do
        echo "Extension $ext info:"
        echo "  number of files: ${extensions_count[$ext]}"
        echo "  overall size of files: ${extensions_sizes[$ext]}"
        echo ""
    done
else
    echo "Parent directory does not contain any files"
fi
