class TrackError(ValueError):
    def __init__(self, code, status=422):
        self.code = code
        self.status = status
        super().__init__(code)
