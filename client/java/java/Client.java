import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Scanner;

public class Client {
    private List<ServerInfo> servers;

    public Client(List<ServerInfo> servers) {
        this.servers = servers;
    }

    public void runClient() {
        Scanner scanner = new Scanner(System.in);
        while (true) {
            System.out.println("---- Client Menu ----");
            System.out.println("1. Push");
            System.out.println("2. Pull");
            System.out.println("3. Subscribe");
            System.out.println("4. Exit");
            System.out.print("Enter your choice: ");
            String choice = scanner.nextLine();

            switch (choice) {
                case "1":
                    System.out.print("Enter key: ");
                    String key = scanner.nextLine();
                    System.out.print("Enter value: ");
                    String val = scanner.nextLine();
                    push(key, val);
                    System.out.println("Pushed " + key + ":" + val + " to server");
                    break;
                case "2":
                    String[] keyValue = pull();
                    if (keyValue[0].isEmpty()) { // error while receiving response
                        break;
                    }
                    System.out.println("Got key:value pair -> " + keyValue[0] + ":" + keyValue[1]);
                    break;
                case "3":
                    TwoStringArgOperator operator = (String k, String v) ->
                            System.out.println("[Subscribed] got key:value pair -> " + k + " " + v);
                    new Thread(new Subscriber(this, operator)).start();
                    break;
                case "4":
                    scanner.close();
                    return;
                default:
                    System.out.println("Invalid choice");
            }
        }
    }

    public String[] pull() {
        Optional<StringBuilder> response = sendRequest("pull", "");
        if (response.isPresent()) {
            try {
                String[] keyValue = response.get().toString().split(":");
                return keyValue;
            } catch (Exception e) {
                System.out.println("Could not parse the response {" + response + "}:\n" + e.getMessage());
                return new String[2];
            }
        } else {
            return new String[2];
        }
    }


    private void push(String key, String val) {
        sendRequest("push", ":" + key + ":" + val); // this call returns null, no further action required
    }

    private Optional<StringBuilder> sendRequest(String type, String data) {
        try (
                Socket client = new Socket(servers.get(0).getIp(), servers.get(0).getPort());
                PrintWriter out = new PrintWriter(client.getOutputStream(), true);
                BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
        ) {
            return Optional.ofNullable(exchange(out, in, type, data));
        } catch (IOException e) {
            System.out.println("Error connecting to the primary load balancer, retrying with the backup LB:\n" + e.getMessage());
            try (
                    Socket client = new Socket(servers.get(1).getIp(), servers.get(1).getPort());
                    PrintWriter out = new PrintWriter(client.getOutputStream(), true);
                    BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
            ) {
                return Optional.ofNullable(exchange(out, in, type, data));
            } catch (IOException e1) {
                System.out.println("Error connecting to the backup load balancer:\n" + e1.getMessage());
                System.out.println("Ignoring request...");
                return Optional.empty();
            }
        }
    }

    private StringBuilder exchange(PrintWriter out, BufferedReader in, String type, String data) {
        out.println(type + data);
        if (!type.equals("push")) {
            StringBuilder response = new StringBuilder(128);
            try {
                int charsIn = -1;
                char[] buffer = new char[1024];
                charsIn = in.read(buffer);
                if (charsIn > 0) {
                    response.append(buffer, 0, charsIn);
                    return response;
                }
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
        return new StringBuilder();
    }

}

class Subscriber implements Runnable {
    private Client client;

    private TwoStringArgOperator operator;

    public Subscriber(Client client, TwoStringArgOperator operator) {
        this.client = client;
        this.operator = operator;

    }

    @Override
    public void run() {
        while (true) {
            String[] keyValue = client.pull();
            if (!keyValue[0].isEmpty()) {
                operator.invoke(keyValue[0], keyValue[1]);
            }
        }
    }
}
interface TwoStringArgOperator {
    void invoke(String key, String value);
}


