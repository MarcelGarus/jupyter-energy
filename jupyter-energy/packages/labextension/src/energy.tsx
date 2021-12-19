// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { VDomModel, VDomRenderer } from '@jupyterlab/apputils';
import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import { TextItem } from '@jupyterlab/statusbar';
import {
  ITranslator, nullTranslator, TranslationBundle
} from '@jupyterlab/translation';
import { Poll } from '@lumino/polling';
import React from 'react';
import { resourceItem } from './text';

export class Energy extends VDomRenderer<Energy.Model> {
  constructor(translator?: ITranslator) {
    super(new Energy.Model({ refreshRate: 5000 }));
    this.translator = translator || nullTranslator;
    this._trans = this.translator.load('jupyterlab');
  }

  render(): JSX.Element {
    if (!this.model) {
      return <div></div>;
    }
    let text: string;
    if (this.model.memoryLimit === null) {
      text = this._trans.__(
        'Mem: %1 %2',
        this.model.currentMemory.toFixed(Private.DECIMAL_PLACES),
        this.model.units
      );
    } else {
      text = this._trans.__(
        'Mem: %1 / %2 %3',
        this.model.currentMemory.toFixed(Private.DECIMAL_PLACES),
        this.model.memoryLimit.toFixed(Private.DECIMAL_PLACES),
        this.model.units
      );
    }
    if (!this.model.usageWarning) {
      return (
        <TextItem
          title={this._trans.__('Current memory usage')}
          source={text}
        />
      );
    } else {
      return (
        <TextItem
          title={this._trans.__('Current memory usage')}
          source={text}
          className={resourceItem}
        />
      );
    }
  }

  protected translator: ITranslator;
  private _trans: TranslationBundle;
}

export namespace Energy {
  export class Model extends VDomModel {
    constructor(options: Model.IOptions) {
      super();
      this._poll = new Poll<Private.IMetricRequestResult>({
        factory: () => Private.factory(),
        frequency: {
          interval: options.refreshRate,
          backoff: true,
        },
        name: '@marcelgarus/statusbar:EnergyUsage#metrics',
      });
      this._poll.ticked.connect((poll) => {
        const { payload, phase } = poll.state;
        if (phase === 'resolved') {
          this._updateMetricsValues(payload);
          return;
        }
        if (phase === 'rejected') {
          const oldMetricsAvailable = this._metricsAvailable;
          this._metricsAvailable = false;
          this._currentMemory = 0;
          this._memoryLimit = null;
          this._units = 'B';

          if (oldMetricsAvailable) {
            this.stateChanged.emit();
          }
          return;
        }
      });
    }

    get metricsAvailable(): boolean {
      return this._metricsAvailable;
    }

    get currentMemory(): number {
      return this._currentMemory;
    }

    get memoryLimit(): number | null {
      return this._memoryLimit;
    }

    get units(): MemoryUnit {
      return this._units;
    }

    get usageWarning(): boolean {
      return this._warn;
    }

    dispose(): void {
      super.dispose();
      this._poll.dispose();
    }

    private _updateMetricsValues(
      value: Private.IMetricRequestResult | null
    ): void {
      const oldMetricsAvailable = this._metricsAvailable;
      const oldCurrentMemory = this._currentMemory;
      const oldMemoryLimit = this._memoryLimit;
      const oldUnits = this._units;
      const oldUsageWarning = this._warn;

      if (value === null) {
        this._metricsAvailable = false;
        this._currentMemory = 0;
        this._memoryLimit = null;
        this._units = 'B';
        this._warn = false;
      } else {
        const numBytes = value.rss;
        const memoryLimit = value.limits.memory
          ? value.limits.memory.rss
          : null;
        const [currentMemory, units] = Private.convertToLargestUnit(numBytes);
        const usageWarning = value.limits.memory
          ? value.limits.memory.warn
          : false;

        this._metricsAvailable = true;
        this._currentMemory = currentMemory;
        this._units = units;
        this._memoryLimit = memoryLimit
          ? memoryLimit / Private.MEMORY_UNIT_LIMITS[units]
          : null;
        this._warn = usageWarning;
      }

      if (
        this._currentMemory !== oldCurrentMemory ||
        this._units !== oldUnits ||
        this._memoryLimit !== oldMemoryLimit ||
        this._metricsAvailable !== oldMetricsAvailable ||
        this._warn !== oldUsageWarning
      ) {
        this.stateChanged.emit(void 0);
      }
    }

    private _currentMemory = 0;
    private _memoryLimit: number | null = null;
    private _metricsAvailable = false;
    private _poll: Poll<Private.IMetricRequestResult>;
    private _units: MemoryUnit = 'B';
    private _warn = false;
  }

  export namespace Model {
    export interface IOptions {
      refreshRate: number;
    }
  }

  export type MemoryUnit = 'B' | 'KB' | 'MB' | 'GB' | 'TB' | 'PB';
}

namespace Private {
  export const DECIMAL_PLACES = 2;

  export const MEMORY_UNIT_LIMITS: {
    readonly [U in Energy.MemoryUnit]: number;
  } = {
    B: 1,
    KB: 1024,
    MB: 1048576,
    GB: 1073741824,
    TB: 1099511627776,
    PB: 1125899906842624,
  };

  // Given a number of bytes, converts them to a human-readable format (including GB, TB, etc.)
  export function convertToLargestUnit(numBytes: number): [number, Energy.MemoryUnit] {
    if (numBytes < MEMORY_UNIT_LIMITS.KB) {
      return [numBytes, 'B'];
    } else if (
      MEMORY_UNIT_LIMITS.KB === numBytes ||
      numBytes < MEMORY_UNIT_LIMITS.MB
    ) {
      return [numBytes / MEMORY_UNIT_LIMITS.KB, 'KB'];
    } else if (
      MEMORY_UNIT_LIMITS.MB === numBytes ||
      numBytes < MEMORY_UNIT_LIMITS.GB
    ) {
      return [numBytes / MEMORY_UNIT_LIMITS.MB, 'MB'];
    } else if (
      MEMORY_UNIT_LIMITS.GB === numBytes ||
      numBytes < MEMORY_UNIT_LIMITS.TB
    ) {
      return [numBytes / MEMORY_UNIT_LIMITS.GB, 'GB'];
    } else if (
      MEMORY_UNIT_LIMITS.TB === numBytes ||
      numBytes < MEMORY_UNIT_LIMITS.PB
    ) {
      return [numBytes / MEMORY_UNIT_LIMITS.TB, 'TB'];
    } else {
      return [numBytes / MEMORY_UNIT_LIMITS.PB, 'PB'];
    }
  }

  const SERVER_CONNECTION_SETTINGS = ServerConnection.makeSettings();
  const METRIC_URL = URLExt.join(
    SERVER_CONNECTION_SETTINGS.baseUrl,
    'api/metrics/v1'
  );

  export interface IMetricRequestResult {
    rss: number;
    limits: {
      memory?: {
        rss: number;
        warn: boolean;
      };
    };
  }

  export async function factory(): Promise<IMetricRequestResult> {
    const response = await ServerConnection.makeRequest(
      METRIC_URL,
      {},
      SERVER_CONNECTION_SETTINGS
    );
    return await response.json();
  }
}
