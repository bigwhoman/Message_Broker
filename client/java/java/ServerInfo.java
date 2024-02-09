public class ServerInfo {
    private String ip;
    private int port;

    public ServerInfo(String ip, String port) {
        this.ip = ip;
        this.port = Integer.parseInt(port);
    }

    @Override
    public String toString() {
        return ip + ":" + port;
    }
    public String getIp() {
        return ip;
    }

    public int getPort() {
        return port;
    }

}
