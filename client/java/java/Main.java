import java.util.ArrayList;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        System.out.println("Client is up...\nTarget Servers:\n");
        List<ServerInfo> serverInfos = new ArrayList<>();
        for (String arg : args) {
            List<String> argParts = List.of(arg.split(":"));
            ServerInfo serverInfo = new ServerInfo(argParts.get(0), argParts.get(1));
            serverInfos.add(serverInfo);
            System.out.println(serverInfo);
        }

        Client client = new Client(serverInfos);
        client.runClient();
    }
}
