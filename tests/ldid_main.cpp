// Use the exact ldid object linked into AltServer, with its renamed CLI entry.
int __main(int argc, char* argv[]);
int main(int argc, char* argv[]) { return __main(argc, argv); }
