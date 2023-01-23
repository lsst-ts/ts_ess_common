# This file is part of ts_ess_common.
#
# Developed for the Vera Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["CONFIG_SCHEMA"]

import json

CONFIG_SCHEMA = json.loads(
    """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "devices": {
      "type": "array",
      "minItems": 1,
      "items": [
        {
          "type": "object",
          "properties": {
            "device_type": {
              "enum": [
                "FTDI",
                "Serial"
              ]
            },
            "name": {
              "type": "string"
            },
            "sensor_type": {
              "enum": [
                "CSAT3B",
                "EFM100C",
                "HX85A",
                "HX85BA",
                "LD250",
                "Temperature",
                "Windsonic"
              ]
            },
            "baud_rate": {
              "type": "number",
              "default": 19200
            }
          },
          "allOf": [
            {
              "if": {
                "properties": {
                  "sensor_type": {
                    "const": "Temperature"
                  }
                }
              },
              "then": {
                "properties": {
                  "channels": {
                    "type": "number"
                  }
                },
                "required": [
                  "channels"
                ]
              }
            },
            {
              "if": {
                "properties": {
                  "device_type": {
                    "const": "FTDI"
                  }
                }
              },
              "then": {
                "properties": {
                  "ftdi_id": {
                    "type": "string"
                  }
                },
                "required": [
                  "ftdi_id"
                ]
              }
            },
            {
              "if": {
                "properties": {
                  "device_type": {
                    "const": "Serial"
                  }
                }
              },
              "then": {
                "properties": {
                  "serial_port": {
                    "type": "string"
                  }
                },
                "required": [
                  "serial_port"
                ]
              }
            }
          ],
          "required": [
            "device_type",
            "name",
            "sensor_type",
            "baud_rate"
          ]
        }
      ]
    }
  },
  "required": [
    "devices"
  ],
  "additionalProperties": false
}
    """
)
