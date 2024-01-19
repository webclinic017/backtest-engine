import { PATHS, PATH_KEYS } from "./constants";

export const getDatasetEditorUrl = (datasetName: string) => {
  return (
    PATHS.datasets.editor.replace(PATH_KEYS.dataset, datasetName) +
    getQueryParamDefaultTab(1)
  );
};

export const getQueryParamDefaultTab = (idx: number) => {
  return `?defaultTab=${idx}`;
};

export const getDatasetColumnInfo = (
  datasetName: string,
  columnName: string
) => {
  return PATHS.datasets.column
    .replace(PATH_KEYS.dataset, datasetName)
    .replace(PATH_KEYS.column, columnName);
};
