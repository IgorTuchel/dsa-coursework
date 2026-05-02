import sys
import time
import tracemalloc
import uuid
from functools import wraps

import cpuinfo
import psutil

from models.output import HardwareInformation, Output


def monitor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cpu_info = cpuinfo.get_cpu_info()
        memory_info = psutil.virtual_memory()

        tracemalloc.start()
        before_snapshot = tracemalloc.take_snapshot()

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        after_snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()

        time_delta = end - start

        stats_before = before_snapshot.statistics("lineno")
        stats_after = after_snapshot.statistics("lineno")

        total_before = sum(stat.size for stat in stats_before)
        total_after = sum(stat.size for stat in stats_after)

        mem_delta = total_after - total_before

        hardware = HardwareInformation(
            cpu_brand=cpu_info["brand_raw"],
            cpu_cores=psutil.cpu_count(),
            cpu_architecture=cpu_info["arch"],
            cpu_bits=cpu_info["bits"],
            cpu_version=cpu_info["cpuinfo_version"],
            hz_friendly=cpu_info["hz_actual_friendly"],
            platform=sys.platform,
            virtual_memory=memory_info.total,
        )

        output = Output(
            uuid=uuid.uuid4().hex,
            data_used="",
            input_params=result.input_params or None,
            additional_params=result.additional_params or None,
            total_distance=result.total_distance,
            routes=result.routes,
            memory_usage=mem_delta / (1024**2),  # in MB
            time_taken=time_delta,
            hardware_info=hardware,
        )
        return output

    return wrapper
