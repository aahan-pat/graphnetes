# Importing each submodule triggers all @ExtractorRegistry.register decorators within it.
from . import workloads, networking, config, storage, infrastructure
