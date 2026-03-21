#!/bin/bash

# Sample data distribution script for WSL Ubuntu
# Creates: 1 sample, 120 for build, 480 for test

# Set paths (adjust if needed)
SOURCE_DIR="/root/myproject/cv-filtering/data"
SAMPLE_DIR="/root/myproject/cv-filtering/demo/data/sample_1"
BUILD_DIR="/root/myproject/cv-filtering/demo/data/build_120"
TEST_DIR="/root/myproject/cv-filtering/demo/data/test_480"

# Colors for output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GRAY='\033[1;30m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Starting data sampling ===${NC}"

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory $SOURCE_DIR does not exist"
    exit 1
fi

# Create output directories
mkdir -p "$SAMPLE_DIR" "$BUILD_DIR" "$TEST_DIR"

# Get all categories (subdirectories in data folder)
CATEGORIES=($(find "$SOURCE_DIR" -maxdepth 1 -type d -exec basename {} \; | grep -v "^.$" | grep -v "^data$"))

echo -e "${CYAN}Found categories: ${#CATEGORIES[@]}${NC}"
printf '%s\n' "${CATEGORIES[@]}"

# Sample 1: Just 1 random PDF from first category
echo -e "${YELLOW}[1/3] Sampling 1 PDF for quick test...${NC}"
FIRST_CATEGORY="${CATEGORIES[0]}"
FIRST_CAT_PATH="$SOURCE_DIR/$FIRST_CATEGORY"

# Check if first category has PDFs
if [ -d "$FIRST_CAT_PATH" ]; then
    PDF_FILES=($(find "$FIRST_CAT_PATH" -name "*.pdf"))
    if [ ${#PDF_FILES[@]} -gt 0 ]; then
        # Select random PDF
        RANDOM_PDF="${PDF_FILES[$RANDOM % ${#PDF_FILES[@]}]}"
        cp "$RANDOM_PDF" "$SAMPLE_DIR/"
        echo -e "${GREEN}OK Sampled: $(basename "$RANDOM_PDF")${NC}"
    else
        echo "Warning: No PDF files found in $FIRST_CAT_PATH"
    fi
else
    echo "Warning: First category directory $FIRST_CAT_PATH does not exist"
fi

# Sample 120: 5 from each category
echo -e "${YELLOW}[2/3] Sampling 120 PDFs (5 per category) for build...${NC}"
BUILD_COUNT=0
for CAT in "${CATEGORIES[@]}"; do
    CAT_PATH="$SOURCE_DIR/$CAT"
    if [ -d "$CAT_PATH" ]; then
        PDF_FILES=($(find "$CAT_PATH" -name "*.pdf"))
        COUNT=$((${#PDF_FILES[@]} < 5 ? ${#PDF_FILES[@]} : 5))
        
        if [ $COUNT -gt 0 ]; then
            # Randomly select PDFs
            for ((i=0; i<COUNT; i++)); do
                if [ ${#PDF_FILES[@]} -gt 0 ]; then
                    RANDOM_IDX=$((RANDOM % ${#PDF_FILES[@]}))
                    RANDOM_PDF="${PDF_FILES[$RANDOM_IDX]}"
                    cp "$RANDOM_PDF" "$BUILD_DIR/"
                    unset PDF_FILES[$RANDOM_IDX]
                    PDF_FILES=("${PDF_FILES[@]}") # Re-index array
                    ((BUILD_COUNT++))
                fi
            done
        fi
        echo -e "  ${GRAY}$CAT : $COUNT PDFs${NC}"
    fi
done
echo -e "${GREEN}OK Total build samples: $BUILD_COUNT${NC}"

# Sample 480: 20 from each category
echo -e "${YELLOW}[3/3] Sampling 480 PDFs (20 per category) for test...${NC}"
TEST_COUNT=0
for CAT in "${CATEGORIES[@]}"; do
    CAT_PATH="$SOURCE_DIR/$CAT"
    if [ -d "$CAT_PATH" ]; then
        PDF_FILES=($(find "$CAT_PATH" -name "*.pdf"))
        COUNT=$((${#PDF_FILES[@]} < 20 ? ${#PDF_FILES[@]} : 20))
        
        if [ $COUNT -gt 0 ]; then
            # Randomly select PDFs
            for ((i=0; i<COUNT; i++)); do
                if [ ${#PDF_FILES[@]} -gt 0 ]; then
                    RANDOM_IDX=$((RANDOM % ${#PDF_FILES[@]}))
                    RANDOM_PDF="${PDF_FILES[$RANDOM_IDX]}"
                    cp "$RANDOM_PDF" "$TEST_DIR/"
                    unset PDF_FILES[$RANDOM_IDX]
                    PDF_FILES=("${PDF_FILES[@]}") # Re-index array
                    ((TEST_COUNT++))
                fi
            done
        fi
        echo -e "  ${GRAY}$CAT : $COUNT PDFs${NC}"
    fi
done
echo -e "${GREEN}OK Total test samples: $TEST_COUNT${NC}"

echo -e "${GREEN}=== Sampling Complete ===${NC}"
SAMPLE_COUNT=$(find "$SAMPLE_DIR" -name "*.pdf" | wc -l)
echo -e "${CYAN}sample_1: $SAMPLE_COUNT${NC}"
echo -e "${CYAN}build_120: $BUILD_COUNT${NC}"
echo -e "${CYAN}test_480: $TEST_COUNT${NC}"