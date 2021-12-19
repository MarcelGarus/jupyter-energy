import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { IStatusBar } from '@jupyterlab/statusbar';
import { ITranslator } from '@jupyterlab/translation';
import { Energy } from './energy';

const extension: JupyterFrontEndPlugin<void> = {
  id: '@marcelgarus/jupyter-energy:energy-status-item',
  autoStart: true,
  requires: [IStatusBar, ITranslator],
  activate: (
    app: JupyterFrontEnd,
    statusBar: IStatusBar,
    translator: ITranslator
  ) => {
    const item = new Energy(translator);

    statusBar.registerStatusItem(extension.id, {
      item,
      align: 'left',
      rank: 2,
      isActive: () => item.model.metricsAvailable,
      activeStateChanged: item.model.stateChanged,
    });
  },
};

export default extension;
