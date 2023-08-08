CURRENT_DIR=$(cd $(dirname $0); pwd);
echo ${CURRENT_DIR};
user_data_dir="${CURRENT_DIR}/user_data";
echo ${user_data_dir};
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --user-data-dir="${user_data_dir}";
echo "started...";