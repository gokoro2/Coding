
#BATCH IVEON TO SLICER CONVERTER


import os
import logging

#logging
logging.basicConfig(
    filename='conversion_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

#Batch conversion function

def convert_images_in_folder(input_folder):
    output_folder = os.path.join(input_folder, "converted_nhdr")
    os.makedirs(output_folder, exist_ok=True)

    files = os.listdir(input_folder)

    # Find all .hdr files
    hdr_files = [f for f in files if f.lower().endswith(".hdr")]

    logging.info(f"Found {len(hdr_files)} header files")

    for hdr_file in hdr_files:
        hdr_path = os.path.join(input_folder, hdr_file)
        base_name = hdr_file[:-4]  # remove ".hdr"

        img_path = os.path.join(input_folder, base_name)

        # Check if corresponding raw image exists
        if not os.path.exists(img_path):
            logging.warning(f"Missing raw image for {hdr_file}. Skipping.")
            continue

        logging.info(f"Processing dataset: {base_name}")
        convert_inveon_to_nhdr(hdr_path, img_path, output_folder)


#Conversion function
def convert_inveon_to_nhdr(hdr_file, img_file, output_folder):
    try:
        with open(hdr_file, "r") as f:
            lines = f.readlines()

        # Defaults
        x_dim = y_dim = z_dim = None
        x_spacing = y_spacing = z_spacing = None
        data_type = None

        # Parse header
        for line in lines:
            parts = line.split()
            if not parts:
                continue

            if parts[0] == "data_type":
                data_type = parts[1]
            elif parts[0] == "x_dimension":
                x_dim = parts[1]
            elif parts[0] == "y_dimension":
                y_dim = parts[1]
            elif parts[0] == "z_dimension":
                z_dim = parts[1]
            elif parts[0] == "pixel_size_x":
                x_spacing = parts[1]
            elif parts[0] == "pixel_size_y":
                y_spacing = parts[1]
            elif parts[0] == "pixel_size_z":
                z_spacing = parts[1]

        if None in [x_dim, y_dim, z_dim, x_spacing, y_spacing, z_spacing]:
            logging.error(f"Missing metadata in {hdr_file}. Skipping.")
            return

        nrrd_type = "int16" if data_type == "2" else "float"

        base_name = os.path.basename(hdr_file).replace(".hdr", "")
        nhdr_name = f"{base_name}.nhdr"
        nhdr_path = os.path.join(output_folder, nhdr_name)

        nhdr = [
            "NRRD0001\n",
            f"type: {nrrd_type}\n",
            "dimension: 3\n",
            f"sizes: {x_dim} {y_dim} {z_dim}\n",
            f"spacings: {x_spacing} {y_spacing} {z_spacing}\n",
            "encoding: raw\n",
            f"data file: {base_name}\n",
            "endian: little\n"
        ]

        with open(nhdr_path, "w") as f:
            f.writelines(nhdr)

        logging.info(f"Saved NHDR: {nhdr_path}")

    except Exception as e:
        logging.error(f"Failed converting {hdr_file}: {e}")


#Data Path
def main():
    input_folder = r"PATH_TO_YOUR_INVEON_FOLDER"
    convert_images_in_folder(input_folder)


if __name__ == "__main__":
    main()
