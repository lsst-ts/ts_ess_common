# This file is part of ts_ess_common.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
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

__all__ = ["RPiDataClient"]

from typing import Any

import yaml

from .controller_data_client import ControllerDataClient


class RPiDataClient(ControllerDataClient):
    """Get environmental data from a Raspberry Pi with custom hat.

    Parameters
    ----------
    name : str
    config : types.SimpleNamespace
        The configuration, after validation by the schema returned
        by `get_config_schema` and conversion to a types.SimpleNamespace.
    topics : `salobj.Controller` or `types.SimpleNamespace`
        The telemetry topics this data client can write,
        as a struct with attributes such as ``tel_temperature``.
    log : `logging.Logger`
        Logger.
    simulation_mode : `int`, optional
        Simulation mode; 0 for normal operation.
    """

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        return yaml.safe_load(
            """
$schema: http://json-schema.org/draft-07/schema#
description: Schema for RPiDataClient
type: object
properties:
  host:
    description: IP address of the TCP/IP interface.
    type: string
    format: hostname
  port:
    description: Port number of the TCP/IP interface.
    type: integer
    default: 5000
  max_read_timeouts:
    description: Maximum number of read timeouts before an exception is raised.
    type: integer
    default: 5
  devices:
    type: array
    minItems: 1
    items:
      type: object
      properties:
        name:
          description: Name of the sensor.
          type: string
        sensor_type:
          description: Type of the sensor.
          type: string
          enum:
          - CSAT3B
          - HX85A
          - HX85BA
          - Temperature
          - Windsonic
        channels:
          description: Number of channels.
          type: integer
        device_type:
          description: Type of the device.
          type: string
          enum:
          - FTDI
          - Serial
        baud_rate:
          description: Baud rate of the sensor.
          type: integer
          default: 19200
        location:
          description: >-
            The location of the device. In case of a multi-channel device with
            probes that can be far away from the sensor, a comma separated line
            can be used to give the location of each probe. In that case the
            locations should be given in the order of the channels.
          type: string
        num_samples:
          description: >-
            Number of samples per telemetry sample. Only relevant for
            certain kinds of data, such as wind speed and direction.
            Ignored for other kinds of data.
          type: integer
          minimum: 2
      anyOf:
      - if:
          properties:
            device_type:
              const: FTDI
        then:
          properties:
            ftdi_id:
              description: FTDI Serial ID to connect to.
              type: string
      - if:
          properties:
            device_type:
              const: Serial
        then:
          properties:
            serial_port:
              description: Serial port to connect to.
              type: string
      required:
        - name
        - sensor_type
        - device_type
        - baud_rate
        - location
required:
  - host
  - port
  - max_read_timeouts
  - devices
additionalProperties: false
"""
        )
