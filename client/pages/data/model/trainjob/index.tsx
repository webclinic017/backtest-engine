import React from "react";
import { useTrainJobDetailed } from "../../../../clients/queries/queries";
import { usePathParams } from "../../../../hooks/usePathParams";
import { Spinner } from "@chakra-ui/react";
import { DOM_EVENT_CHANNELS, PATHS } from "../../../../utils/constants";
import { Breadcrumbs } from "../../../../components/chakra/Breadcrumbs";
import {
  getDatasetInfoPagePath,
  getModelInfoPath,
} from "../../../../utils/navigate";
import { TrainjobInfoPage } from "./info";
import { ChakraTabs } from "../../../../components/layout/Tabs";
import { useMessageListener } from "../../../../hooks/useMessageListener";
import { BacktestModelPage } from "./backtest";

const TAB_LABELS = ["Info", "Simulate"];
const TABS = [<TrainjobInfoPage key={0} />, <BacktestModelPage key={1} />];

export const TrainJobIndex = () => {
  const { trainJobId } = usePathParams<{
    trainJobId: string;
    datasetName?: string;
  }>();

  const { data, refetch } = useTrainJobDetailed(trainJobId);

  useMessageListener({
    messageName: DOM_EVENT_CHANNELS.refetch_component,
    messageCallback: refetch,
  });

  if (!data)
    return (
      <div>
        <Spinner />
      </div>
    );
  return (
    <div style={{ paddingTop: "16px" }}>
      <Breadcrumbs
        items={[
          { label: "Data", href: PATHS.data.index },
          {
            label: "Dataset",
            href: getDatasetInfoPagePath(data.dataset.dataset_name),
          },
          {
            label: "Models",
            href: getModelInfoPath(
              data.dataset.dataset_name,
              data.model.model_name
            ),
          },
          { label: "Training", href: "test" },
        ]}
      />
      <ChakraTabs labels={TAB_LABELS} tabs={TABS} />
    </div>
  );
};
